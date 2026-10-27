"""Test the production sentiment query without modifying application data."""
import json,re,sqlite3
from pathlib import Path
conn=sqlite3.connect(':memory:')
conn.execute('CREATE TABLE picks (owner TEXT,game_id TEXT,market TEXT,side INTEGER,mode TEXT,legs TEXT)')
def add(owner,market,side=0,legs=None,mode='live'):
    conn.execute('INSERT INTO picks VALUES (?,?,?,?,?,?)',(owner,'game',market,side,mode,json.dumps(legs) if legs is not None else None))
def leg(market='moneyline',side=0):return dict(gameId='game',market=market,side=side)
add('a','moneyline')
add('a','parlay',legs=[leg(),leg('spread'),leg('pts')])
add('a','parlay',legs=[leg(),leg('spread')])
add('b','parlay',legs=[leg(),leg('total',1)])
add('c','parlay',legs=[leg(side=1)])
add('a','parlay',legs=[leg(side=1)])
add('demo','parlay',legs=[leg()],mode='demo')
add('empty','parlay')
conn.execute("INSERT INTO picks VALUES ('bad','x','parlay',0,'live','broken json')")
sql=re.search(r'const sentiment=.*?prepare\("(.*?)"\)',Path('lib/store.ts').read_text()).group(1)
rows={(game,market,side):count for game,market,side,count in conn.execute(sql,['live','live'])}
assert rows=={('game','moneyline',0):2,('game','moneyline',1):2,('game','spread',0):1,('game','total',1):1},rows
print('PASS: singles and parlay legs, unique fan-side counts, opposing selections, mode isolation, prop exclusion, empty/malformed legs.')
