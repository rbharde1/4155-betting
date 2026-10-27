"""Check actual endpoint balance guards and leaderboard SQL in isolated SQLite."""
import re, sqlite3
from pathlib import Path
week=('2026-10-26T04:00:00.000Z','2026-11-02T05:00:00.000Z')
for route in ['picks','model-props','player-props','parlays']:
    text=Path(f'app/api/{route}/route.ts').read_text()
    sql=re.search(r'prepare\("(INSERT INTO picks .*?)"\)',text).group(1)
    cols=[c.strip() for c in sql.split('(',1)[1].split(')',1)[0].split(',')]
    selects=sql.split(' SELECT ',1)[1].split(' WHERE ',1)[0].split(',')
    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE picks ('+','.join(c+' '+('INTEGER' if c.endswith('_cents') else 'TEXT') for c in cols)+')')
    values=dict(id='test',owner='user',game_id='game',mode='live',market='moneyline',side=0,label='pick',matchup='a at b',odds=-110,point=1,stake_cents=1000,profit_cents=909,source='test',fetched_at=week[0],start='2099-01-01T00:00:00Z',created_at=week[0],player_prop='{}',legs='[]')
    args=[values[c] for c,v in zip(cols,selects) if v=='?']
    guard=[1000,'user']+([] if route=='model-props' else ['live'])+list(week)+(['live',values['start']] if route=='parlays' else [])
    # Previous-week stakes must not consume this week's allocation.
    conn.execute("INSERT INTO picks (owner,mode,result,stake_cents,created_at) VALUES ('user','live','pending',100000,'2026-10-20T00:00:00Z')")
    for i in range(10):assert conn.execute(sql,args+guard).rowcount==1,route
    assert conn.execute(sql,args+guard).rowcount==0,route
    assert 'MAX_STAKE' not in text,route
    conn.execute('DELETE FROM picks')
    large=args.copy();large[[c for c,v in zip(cols,selects) if v=="?"].index('stake_cents')]=10000
    full=guard.copy();full[0]=10000
    assert conn.execute(sql,large+full).rowcount==1,route
    assert conn.execute(sql,args+guard).rowcount==0,route
conn=sqlite3.connect(':memory:')
conn.execute('CREATE TABLE picks (owner TEXT,mode TEXT,result TEXT,created_at TEXT,stake_cents INTEGER,profit_cents INTEGER)')
for owner,count,result,date in [('qualified',1,'won',week[0]),('unqualified',4,'pending',week[0]),('pushes',5,'push',week[0]),('old',5,'won','2026-10-20T00:00:00Z')]:
    conn.executemany('INSERT INTO picks VALUES (?,?,?,?,?,?)',[(owner,'live',result,date,1000,909)]*count)
sql=re.search(r'const leaders=.*?prepare\("(.*?)"\)',Path('lib/store.ts').read_text()).group(1)
assert [r[0] for r in conn.execute(sql,['live',*week,1])]==['qualified']
print('PASS: all four atomic weekly balance guards, limits, and weekly leaderboard eligibility.')
