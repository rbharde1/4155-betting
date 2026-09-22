import {db,user,state,sameOrigin} from '@/lib/store';
import {games,quote,Market} from '@/lib/basketball';
import {liveBoard} from '@/lib/espn';
import {ParlayLeg,americanOdds,combinedDecimal,parlayProfitCents} from '@/lib/parlay';
export async function POST(request:Request){
 if(!sameOrigin(request))return Response.json({error:'Invalid request origin.'},{status:403});
 try{
  const owner=await user();const b:any=await request.json();
  if(!['live','demo'].includes(b.mode)||typeof b.id!=='string'||!/^[\w-]{16,64}$/.test(b.id)||typeof b.stake!=='number'||!Number.isFinite(b.stake)||b.stake<1||b.stake>1000||Math.abs(b.stake*100-Math.round(b.stake*100))>0.00001)return Response.json({error:'Enter a valid paper stake from 1 to 1,000 points with at most two decimals.'},{status:400});
  if(!Array.isArray(b.legs)||b.legs.length<2||b.legs.length>6||b.legs.some((l:any)=>!l||typeof l.gameId!=='string'||!['moneyline','spread','total'].includes(l.market)||![0,1].includes(l.side)))return Response.json({error:'Choose 2–6 valid legs for your parlay.'},{status:400});
  if(new Set(b.legs.map((l:any)=>l.gameId)).size!==b.legs.length)return Response.json({error:'Choose only one leg per game. Same-game parlays are not supported.'},{status:400});
  const prior=await db().prepare('SELECT id,mode,market FROM picks WHERE id=? AND owner=?').bind(b.id,owner).first<any>();
  if(prior){if(prior.mode!==b.mode||prior.market!=='parlay')return Response.json({error:'This submission ID belongs to another wager.'},{status:409});return Response.json({id:b.id,...await state(b.mode,owner)});}
  const list=b.mode==='demo'?games:(await liveBoard()).games;const now=new Date().toISOString();const legs:ParlayLeg[]=[];
  for(const leg of b.legs){
   const g=list.find(g=>g.id===leg.gameId);
   if(!g||b.mode==='live'&&(!g.start||Date.parse(g.start)<=Date.now()||!g.fetchedAt||Date.now()-Date.parse(g.fetchedAt)>120000))return Response.json({error:'A leg is locked or no longer available. Refresh the board and replace it.'},{status:409});
   const q=quote(g,leg.market as Market,leg.side);
   if(q.odds!==leg.odds||q.point!==leg.point)return Response.json({error:`The line moved for ${g.awayCode} at ${g.homeCode}. Refresh and select that leg again.`},{status:409});
   legs.push({gameId:g.id,market:leg.market,side:leg.side,label:q.label,matchup:`${g.away} at ${g.home}`,odds:q.odds,point:q.point,source:g.source??'Demo simulation',fetchedAt:g.fetchedAt??now,start:g.start??now,result:'pending'});
  }
  const key=legs.map(l=>`${l.gameId}:${l.market}:${l.side}`).sort().join('|');const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(key));const gameId='parlay:'+Array.from(new Uint8Array(digest)).map(n=>n.toString(16).padStart(2,'0')).join('');
  const cents=Math.round(b.stake*100),odds=legs.map(l=>l.odds),earn=parlayProfitCents(cents,odds);
  if(!Number.isSafeInteger(earn)||earn<0)return Response.json({error:'This combination cannot be priced.'},{status:400});
  const firstStart=legs.map(l=>l.start).sort()[0];
  const inserted=await db().prepare("INSERT INTO picks (id,owner,game_id,mode,market,side,label,matchup,odds,point,stake_cents,profit_cents,result,source,fetched_at,start,created_at,legs) SELECT ?,?,?,?,'parlay',0,?,?,?,NULL,?,?,'pending',?,?,?,?,? WHERE ? <= 100000 + COALESCE((SELECT SUM(CASE WHEN result='pending' THEN -stake_cents WHEN result='won' THEN profit_cents WHEN result='lost' THEN -stake_cents ELSE 0 END) FROM picks WHERE owner=? AND mode=?),0) AND (?='demo' OR julianday(?)>julianday('now'))").bind(b.id,owner,gameId,b.mode,`${legs.length}-leg parlay`,legs.map(l=>l.label).join(' + '),americanOdds(combinedDecimal(odds)),cents,earn,'Courtside combined paper odds',now,firstStart,now,JSON.stringify(legs),cents,owner,b.mode,b.mode,firstStart).run();
  if(!inserted.meta.changes)return Response.json({error:'Insufficient paper balance or a game has started.'},{status:409});
  return Response.json({id:b.id,...await state(b.mode,owner)},{status:201});
 }catch(e){const message=(e as Error).message;return Response.json({error:message.includes('UNIQUE')?'You already locked this parlay combination.':message.includes('Sign in')?message:'Could not save the parlay. Your selections are kept; please retry.'},{status:message.includes('UNIQUE')?409:503});}
}
