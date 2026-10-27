"""Local mixed parlay checks. Cleanup SQL targets only this run's test tickets."""
import json,uuid,urllib.request,urllib.error,http.cookiejar
from pathlib import Path
base='http://localhost:5173'
s=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
s.open(base+'/signin-with-chatgpt?return_to=/dashboard').read()
def req(path,b=None):
 r=urllib.request.Request(base+path,data=None if b is None else json.dumps(b).encode(),headers={'Content-Type':'application/json','Origin':base})
 try:
  with s.open(r,timeout=30) as x:return x.status,json.load(x)
 except urllib.error.HTTPError as x:return x.code,json.load(x)
_,initial=req('/api/picks?mode=live');assert initial['balance']>=3
_,board=req('/api/board?mode=live');found=None
for game in board['games']:
 status,data=req('/api/model-props?gameId='+game['id'])
 if status==200 and len(data['players'])>2:found=(game,data['players']);break
assert found,'No upcoming CSV matchup available.'
game,players=found
# Choose a player without a preexisting test combination.
player=players[-1]
def prop(market,side=0):return dict(kind='model',gameId=game['id'],playerId=player['playerId'],market=market,side=side,point=player['markets'][market]['line'],odds=-110)
team=dict(gameId=game['id'],market='moneyline',side=0,point=None,odds=game['awayOdds'])
ids=[]
def ticket(legs):
 id='qa-mixed-'+uuid.uuid4().hex;ids.append(id)
 return dict(id=id,mode='live',stake=1,legs=legs)
try:
 assert req('/api/parlays',ticket([prop('pts'),prop('pts',1)]))[0]==400
 assert req('/api/parlays',ticket([prop('pts'),prop('pts')]))[0]==400
 assert req('/api/parlays',ticket([prop('pts'),dict(kind='player',gameId=game['id'],playerId=player['playerId'],market='points',side=1,point=19.5,odds=-110,propId='test')]))[0]==400
 assert req('/api/parlays',ticket([team,{**team,'side':1}]))[0]==400
 assert req('/api/parlays',ticket([team,{**prop('pts'),'odds':100}]))[0]==409
 assert req('/api/parlays',ticket([team,{**prop('pts'),'point':999}]))[0]==409
 assert req('/api/parlays',ticket([{**team,'gameId':'old-game'},prop('pts')]))[0]==409
 for i,legs in enumerate([[team,prop('pts')],[prop('pr'),prop('pra',1)]]):
  b=ticket(legs);status,data=req('/api/parlays',b);assert status==201,(status,data)
  p=next(p for p in data['history'] if p['id']==b['id']);assert len(p['legs'])==2
  assert any(l.get('playerProp',{}).get('kind')=='model' for l in p['legs'])
  if i==1:assert p['profit_cents']==264 and p['odds']==264
  assert data['balance']==initial['balance']-i-1
  assert req('/api/parlays',b)[0]==200
  assert req('/api/parlays',ticket(list(reversed(legs))))[0]==409
 print('PASS: mixed team/player and same-game player parlays, -110 payout, snapshots, bankroll, idempotency, duplicate combinations, opposite-side rejection across feeds, tampered lines and missing games.')
finally:
 Path('/private/tmp/courtside-mixed-cleanup.sql').write_text('DELETE FROM picks WHERE id IN ('+','.join("'"+i+"'" for i in ids)+');')
