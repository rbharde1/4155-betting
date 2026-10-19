"""Local integration test. Requires empty practice history; writes exact cleanup SQL."""
import json,uuid,urllib.request,urllib.error,http.cookiejar
from pathlib import Path
base='http://localhost:5173'
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
client.open(base+'/signin-with-chatgpt?return_to=/').read()
ids=[]
def request(path,body=None):
    req=urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','Origin':base})
    try:
        with client.open(req,timeout=40) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
_,before=request('/api/picks?mode=demo')
assert not before['history'],'Requires empty local practice history.'
_,board=request('/api/player-props?mode=demo&gameId=demo-bos-nyk')
assert len(board['props'])==18
try:
    for stat in ['points','assists','rebounds']:
        p=next(p for p in board['props'] if p['stat']==stat)
        b=dict(id='qa-props-'+uuid.uuid4().hex,mode='demo',gameId='demo-bos-nyk',propId=p['id'],side=1,line=p['line'],odds=p['under'],stake=10)
        ids.append(b['id'])
        assert request('/api/player-props',{**b,'odds':999})[0]==409
        assert request('/api/player-props',{**b,'stake':1.005})[0]==400
        status,result=request('/api/player-props',b);assert status==201,(status,result)
        assert request('/api/player-props',b)[0]==200
        assert request('/api/player-props',{**b,'id':'qa-props-'+uuid.uuid4().hex})[0]==409
    _,state=request('/api/picks?mode=demo');assert state['balance']==970 and state['pending']==3
    assert not state['sentiment']
    status,state=request('/api/settle',{'mode':'demo'});assert status==200 and state['pending']==0 and state['balance']==1027.27,state
    assert all(p['result']=='won' for p in state['history'])
    _,again=request('/api/settle',{'mode':'demo'});assert again['balance']==1027.27
    print('PASS: all three player markets, tampered odds, invalid stake, idempotency, duplicates, bankroll, sentiment exclusion, settlement and repeated settlement.')
finally:
    Path('/private/tmp/courtside-prop-cleanup.sql').write_text('DELETE FROM picks WHERE id IN ('+','.join("'"+i+"'" for i in ids)+');')
