import {competitionWeek} from '@/lib/weekly';
import {preferSpread} from '@/lib/selection-rules';
import csv from '@/ml/data/processed/nba_prop_predictions.csv?raw';
import {parseModelProps,matchModelGame} from '@/lib/model-props';
import {playerBoard} from '@/lib/bdl';
import {marketKey} from '@/lib/slip';
import {db,user,state,sameOrigin} from '@/lib/store';
import {games,quote,Market} from '@/lib/basketball';
import {liveBoard} from '@/lib/espn';
import {ParlayLeg,americanOdds,combinedDecimal,parlayProfitCents} from '@/lib/parlay';
export async function POST(request:Request){
 if(!sameOrigin(request))return Response.json({error:'Invalid request origin.'},{status:403});
 try{
  const owner=await user();const b:any=await request.json();
  if(!['live'].includes(b.mode)||typeof b.id!=='string'||!/^[\w-]{16,64}$/.test(b.id)||typeof b.stake!=='number'||!Number.isFinite(b.stake)||b.stake<1||Math.abs(b.stake*100-Math.round(b.stake*100))>0.00001)return Response.json({error:'Enter a valid paper stake of at least 1 point with at most two decimals.'},{status:400});
  if(!Array.isArray(b.legs)||b.legs.length<2||b.legs.length>6||b.legs.some((l:any)=>!l||typeof l.gameId!=='string'||!(l.kind==='model'?['pts','pr','pra']:l.kind==='player'?['points','assists','rebounds']:['moneyline','spread','total']).includes(l.market)||l.kind!=null&&!['model','player'].includes(l.kind)||l.kind&&!Number.isSafeInteger(l.playerId)||![0,1].includes(l.side)))return Response.json({error:'Choose 2–6 valid legs for your parlay.'},{status:400});
  if(new Set(b.legs.map(marketKey)).size!==b.legs.length)return Response.json({error:'Choose only one side of each player prop or game market. Over and Under of the same prop cannot be combined.'},{status:400});
  if(preferSpread(b.legs).length!==b.legs.length)return Response.json({error:'Keep only the spread for a team; its moneyline and spread cannot be combined.'},{status:400});
  const prior=await db().prepare('SELECT id,mode,market FROM picks WHERE id=? AND owner=?').bind(b.id,owner).first<any>();
  if(prior){if(prior.mode!==b.mode||prior.market!=='parlay')return Response.json({error:'This submission ID belongs to another wager.'},{status:409});return Response.json({id:b.id,...await state(b.mode,owner)});}
  const list=b.mode==='demo'?games:(await liveBoard()).games;const now=new Date().toISOString();const legs:ParlayLeg[]=[];
  for(const leg of b.legs){
   const g=list.find(g=>g.id===leg.gameId);
   if(!g||b.mode==='live'&&(!g.start||Date.parse(g.start)<=Date.now()||!g.fetchedAt||Date.now()-Date.parse(g.fetchedAt)>120000))return Response.json({error:'A leg is locked or no longer available. Refresh the board and replace it.'},{status:409});
   let q:{label:string;odds:number;point:number|null};let playerProp:any;let source=g.source??'ESPN';
   if(leg.kind==='model'){
    const p=matchModelGame(parseModelProps(csv).players,g).find(p=>p.playerId===leg.playerId);const v=p?.markets[leg.market as 'pts'|'pr'|'pra'];
    if(!p||!v)return Response.json({error:'A model prop is no longer available.'},{status:409});
    q={label:`${p.name} · ${leg.side===0?'Over':'Under'} ${v.line} ${leg.market.toUpperCase()}`,odds:-110,point:v.line};source='CSV model line · Courtside paper odds -110';
    playerProp={kind:'model',eventId:g.id,playerId:p.playerId,providerGameId:p.gameId,name:p.name,home:p.home,market:leg.market,line:v.line,projection:v.projection,overProbability:v.over,underProbability:v.under};
   }else if(leg.kind==='player'){
    const data=await playerBoard(g,'live');const p=data.props.find(p=>p.id===leg.propId&&p.playerId===leg.playerId&&p.stat===leg.market);
    if(!p)return Response.json({error:'A player prop is no longer available.'},{status:409});
    q={label:`${p.player} · ${leg.side===0?'Over':'Under'} ${p.line} ${p.stat}`,odds:leg.side===0?p.over:p.under,point:p.line};playerProp=p;source=data.source;
   }else q=quote(g,leg.market as Market,leg.side);
   if(q.odds!==leg.odds||q.point!==leg.point)return Response.json({error:`The line moved for ${g.awayCode} at ${g.homeCode}. Refresh and select that leg again.`},{status:409});
   legs.push({gameId:g.id,market:leg.market,side:leg.side,label:q.label,matchup:`${g.away} at ${g.home}`,odds:q.odds,point:q.point,kind:leg.kind,playerId:leg.playerId,playerProp,source,fetchedAt:g.fetchedAt??now,start:g.start??now,result:'pending'});
  }
  const key=legs.map(l=>`${marketKey(l)}:${l.side}`).sort().join('|');const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(key));const gameId='parlay:'+Array.from(new Uint8Array(digest)).map(n=>n.toString(16).padStart(2,'0')).join('');
  const cents=Math.round(b.stake*100),odds=legs.map(l=>l.odds),earn=parlayProfitCents(cents,odds);
  if(!Number.isSafeInteger(earn)||earn<0)return Response.json({error:'This combination cannot be priced.'},{status:400});
  const firstStart=legs.map(l=>l.start).sort()[0];
  const week=competitionWeek(new Date(now));
 const inserted=await db().prepare("INSERT INTO picks (id,owner,game_id,mode,market,side,label,matchup,odds,point,stake_cents,profit_cents,result,source,fetched_at,start,created_at,legs) SELECT ?,?,?,?,'parlay',0,?,?,?,NULL,?,?,'pending',?,?,?,?,? WHERE ? <= 10000 + COALESCE((SELECT SUM(CASE WHEN result='pending' THEN -stake_cents WHEN result='won' THEN profit_cents WHEN result='lost' THEN -stake_cents ELSE 0 END) FROM picks WHERE owner=? AND mode=? AND created_at>=? AND created_at<?),0) AND (?='demo' OR julianday(?)>julianday('now'))").bind(b.id,owner,gameId,b.mode,`${legs.length}-leg parlay`,legs.map(l=>l.label).join(' + '),americanOdds(combinedDecimal(odds)),cents,earn,'Courtside combined paper odds',now,firstStart,now,JSON.stringify(legs),cents,owner,b.mode,week.start,week.end,b.mode,firstStart).run();
  if(!inserted.meta.changes)return Response.json({error:'Insufficient paper balance or a game has started.'},{status:409});
  return Response.json({id:b.id,...await state(b.mode,owner)},{status:201});
 }catch(e){const message=(e as Error).message;return Response.json({error:message.includes('UNIQUE')?'You already locked this parlay combination.':message.includes('Sign in')?message:'Could not save the parlay. Your selections are kept; please retry.'},{status:message.includes('UNIQUE')?409:503});}
}
