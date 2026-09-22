#!/usr/bin/env python3
"""Integration checks against a fresh LOCAL preview. Creates practice test picks only."""
import concurrent.futures
import http.cookiejar
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path
BASE='http://localhost:5173'
jar=http.cookiejar.CookieJar()
opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
opener.open(BASE+'/signin-with-chatgpt?return_to=/').read()
prefix='qa-'+uuid.uuid4().hex[:12]+'-'
ids=[]
def req(path,body=None):
    data=json.dumps(body).encode() if body is not None else None
    request=urllib.request.Request(BASE+path,data=data,headers={'Content-Type':'application/json','Origin':BASE})
    try:
        with opener.open(request,timeout=30) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
def pick(game,market,side,odds,point,stake=10):
    id=prefix+uuid.uuid4().hex[:12];ids.append(id)
    return dict(id=id,mode='demo',gameId=game,market=market,side=side,odds=odds,point=point,stake=stake)
_,before=req('/api/picks?mode=demo')
assert not before['history'],'Use a fresh local practice database for this integration suite.'
_,live=req('/api/picks?mode=live'); live_balance=live['balance']
bad=pick('demo-bos-nyk','spread',0,999,-4.5)
assert req('/api/picks',bad)[0]==409
for bad_stake in [-1,0,1.005,1001]:
    bad=pick('demo-bos-nyk','moneyline',0,-185,None,bad_stake)
    assert req('/api/picks',bad)[0]==400
bodies=[pick('demo-bos-nyk','moneyline',0,-185,None),pick('demo-bos-nyk','spread',0,-110,-4.5),pick('demo-bos-nyk','total',0,-110,224.5)]
for body in bodies:assert req('/api/picks',body)[0]==201
status,d=req('/api/picks',bodies[0]);assert status==200 and d['pending']==3 and d['balance']==970
assert req('/api/picks',pick('demo-bos-nyk','moneyline',1,155,None))[0]==409
assert req('/api/picks',pick('demo-lal-gsw','moneyline',0,135,None,980))[0]==409
concurrent_bodies=[pick('demo-lal-gsw','moneyline',0,135,None,600),pick('demo-den-okc','moneyline',0,210,None,600)]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    statuses=list(pool.map(lambda body:req('/api/picks',body)[0],concurrent_bodies))
assert sorted(statuses)==[201,409],statuses
_,d=req('/api/picks?mode=demo');assert d['balance']==370 and len(d['history'])==4
_,after=req('/api/picks?mode=live');assert after['balance']==live_balance
status,d=req('/api/settle',{'mode':'demo'});assert status==200 and d['pending']==0
balance=d['balance'];assert all(p['result'] in ['won','lost','push'] for p in d['history'])
_,again=req('/api/settle',{'mode':'demo'});assert again['count']==0 and again['balance']==balance
assert req('/api/picks',pick('demo-bos-nyk','moneyline',1,155,None))[0]==409
Path('/private/tmp/courtside-test-ids.json').write_text(json.dumps(ids))
print('PASS: all 3 markets, line tampering, invalid stakes, idempotency, duplicates, balance limits, concurrent overspend, persistence, mode isolation, and settlement idempotency.')
print('Local test ID prefix:',prefix)
