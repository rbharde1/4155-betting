"""Checks local model picks; writes cleanup SQL containing only generated test IDs."""
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
 if status==200:
  for player in data['players']:
   if not any(p['game_id']==f"model:{game['id']}:{player['playerId']}" for p in initial['history']):found=(game,player);break
 if found:break
assert found,'No unpicked upcoming CSV matchup available for test.'
game,player=found;ids=[]
try:
 for i,market in enumerate(['pts','pr','pra']):
  body=dict(id='qa-model-'+uuid.uuid4().hex,mode='live',gameId=game['id'],playerId=player['playerId'],market=market,side=i%2,line=player['markets'][market]['line'],odds=-110,stake=1)
  ids.append(body['id'])
  assert req('/api/model-props',{**body,'odds':100})[0]==409
  assert req('/api/model-props',{**body,'line':body['line']+1})[0]==409
  assert req('/api/model-props',{**body,'stake':1.005})[0]==400
  status,result=req('/api/model-props',body);assert status==201,(status,result)
  pick=next(p for p in result['history'] if p['id']==body['id'])
  assert pick['odds']==-110 and pick['profit_cents']==91 and pick['stake_cents']==100
  assert result['balance']==initial['balance']-(i+1)
  assert req('/api/model-props',body)[0]==200
  assert req('/api/model-props',{**body,'id':'qa-model-'+uuid.uuid4().hex,'side':1-body['side']})[0]==409
 print('PASS: PTS/PR/PRA -110 submissions, both sides, immutable line validation, cent precision, duplicates, idempotency and bankroll deductions.')
finally:
 Path('/private/tmp/courtside-model-cleanup.sql').write_text('DELETE FROM picks WHERE id IN ('+','.join("'"+i+"'" for i in ids)+');')
