#!/usr/bin/env python3
"""Parlay integration checks against an empty LOCAL practice database only."""
import concurrent.futures, http.cookiejar, json, urllib.error, urllib.request, uuid
from pathlib import Path
BASE='http://localhost:5173'
jar=http.cookiejar.CookieJar()
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.open(BASE+'/signin-with-chatgpt?return_to=/').read()
ids=[]
def req(path,body=None):
    r=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','Origin':BASE})
    try:
        with opener.open(r,timeout=30) as response:return response.status,json.load(response)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
def identifier():
    id='qa-parlay-'+uuid.uuid4().hex;ids.append(id)
    Path('/private/tmp/courtside-parlay-test-ids.json').write_text(json.dumps(ids))
    return id
def ticket(legs,stake=10):return dict(id=identifier(),mode='demo',stake=stake,legs=legs)
def leg(game,market,side,odds,point=None):return dict(gameId=game,market=market,side=side,odds=odds,point=point)
a=leg('demo-bos-nyk','moneyline',0,-185)
b=leg('demo-lal-gsw','spread',0,-110,3.5)
c=leg('demo-den-okc','total',1,-110,228.5)
_,before=req('/api/picks?mode=demo')
assert not before['history'],'Use an empty local practice database.'
_,live=req('/api/picks?mode=live')
for legs in [[a],[a,b,c,a,b,c,a],[a,leg('demo-bos-nyk','total',0,-110,224.5)]]:
    assert req('/api/parlays',ticket(legs))[0]==400
for stake in [-1,0,1.005,1001]:assert req('/api/parlays',ticket([a,b],stake))[0]==400
assert req('/api/parlays',ticket([dict(a,odds=999),b]))[0]==409
assert req('/api/parlays',ticket([a,dict(b,point=99)]))[0]==409
assert req('/api/parlays',ticket([a,dict(b,gameId='missing')]))[0]==409
body=ticket([a,b,c]);status,d=req('/api/parlays',body)
assert status==201,(status,d)
assert d['balance']==990 and d['pending']==1
p=d['history'][0];assert len(p['legs'])==3 and p['stake_cents']==1000
assert p['profit_cents']==round(1000*((1+100/185)*(1+100/110)**2-1))
assert not d['sentiment'],'Parlay legs should not inflate single-pick sentiment.'
status,retry=req('/api/parlays',body);assert status==200 and retry['balance']==990 and len(retry['history'])==1
assert req('/api/parlays',ticket([c,b,a]))[0]==409
assert req('/api/parlays',ticket([a,b],1000))[0]==409
other=ticket([a,leg('demo-mil-cle','moneyline',0,180)],600)
single=dict(id=identifier(),mode='demo',stake=600,**leg('demo-lal-gsw','moneyline',0,135))
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(req,'/api/parlays',other),pool.submit(req,'/api/picks',single)]
    statuses=[f.result()[0] for f in futures]
assert sorted(statuses)==[201,409],statuses
_,d=req('/api/picks?mode=demo');assert d['balance']==390 and len(d['history'])==2
_,after=req('/api/picks?mode=live');assert after['balance']==live['balance']
status,d=req('/api/settle',{'mode':'demo'});assert status==200 and d['pending']==0,(status,d)
p=next(p for p in d['history'] if p['id']==body['id']);assert p['result']=='won',p
assert all(l['result']=='won' for l in p['legs']) and all(l['score'] for l in p['legs'])
_,again=req('/api/settle',{'mode':'demo'});assert again['count']==0 and again['balance']==d['balance']
assert req('/api/parlays',ticket([b,c,a]))[0]==409
print('PASS: mixed-market parlay, one stake, saved leg snapshots, validation, moved odds, duplicate order, idempotency, concurrent single/parlay balance protection, persistence, mode isolation and settlement.')
