import {db,user,state,settle,sameOrigin} from '@/lib/store';
import {games,quote,profit,Market} from '@/lib/basketball';
import {liveBoard} from '@/lib/espn';
export const dynamic='force-dynamic';
export async function GET(request:Request){try{const owner=await user();const mode=new URL(request.url).searchParams.get('mode')==='demo'?'demo':'live';if(mode==='live')await settle(mode,owner);return Response.json(await state(mode,owner),{headers:{'Cache-Control':'no-store'}});}catch(e){return Response.json({error:(e as Error).message},{status:503});}}
export async function POST(request:Request){
 if(!sameOrigin(request))return Response.json({error:'Invalid request origin.'},{status:403});
 try{
 const owner=await user();const b:any=await request.json();
 if(!['live','demo'].includes(b.mode)||!['moneyline','spread','total'].includes(b.market)||![0,1].includes(b.side)||typeof b.stake!=='number'||!Number.isFinite(b.stake)||b.stake<1||b.stake>1000||Math.abs(b.stake*100-Math.round(b.stake*100))>0.00001||typeof b.id!=='string'||!/^[\w-]{16,64}$/.test(b.id))return Response.json({error:'Choose a valid pick and a stake from 1 to 1,000 paper points, with at most two decimals.'},{status:400});
 const prior=await db().prepare('SELECT id FROM picks WHERE id=? AND owner=?').bind(b.id,owner).first();if(prior)return Response.json({id:b.id,...await state(b.mode,owner)});
 const list=b.mode==='demo'?games:(await liveBoard()).games;const game=list.find(g=>g.id===b.gameId);if(!game)return Response.json({error:'This game no longer has available pregame lines. Refresh the board.'},{status:409});
 if(b.mode==='live'&&(!game.start||Date.parse(game.start)<=Date.now()||!game.fetchedAt||Date.now()-Date.parse(game.fetchedAt)>120000))return Response.json({error:'This game is locked or its odds are stale. Refresh the board.'},{status:409});
 const q=quote(game,b.market as Market,b.side);if(q.odds!==b.odds||q.point!==b.point)return Response.json({error:'The line moved. Refresh the board and select the updated line.'},{status:409});
 const stake=Math.round(b.stake*100),earn=Math.round(profit(b.stake,q.odds)*100),now=new Date().toISOString();
 const inserted=await db().prepare("INSERT INTO picks (id,owner,game_id,mode,market,side,label,matchup,odds,point,stake_cents,profit_cents,result,source,fetched_at,start,created_at) SELECT ?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?,?,? WHERE ? <= 100000 + COALESCE((SELECT SUM(CASE WHEN result='pending' THEN -stake_cents WHEN result='won' THEN profit_cents WHEN result='lost' THEN -stake_cents ELSE 0 END) FROM picks WHERE owner=? AND mode=?),0)").bind(b.id,owner,game.id,b.mode,b.market,b.side,q.label,`${game.away} at ${game.home}`,q.odds,q.point,stake,earn,game.source??'Demo simulation',game.fetchedAt??now,game.start??now,now,stake,owner,b.mode).run();
 if(!inserted.meta.changes)return Response.json({error:'Not enough paper points available.'},{status:409});
 return Response.json({id:b.id,...await state(b.mode,owner)},{status:201});
 }catch(e){const m=(e as Error).message;return Response.json({error:m.includes('UNIQUE')?'You already locked a pick in this market for this game.':m.includes('Sign in')?m:'Could not save this pick. Your selection has been kept; please retry.'},{status:m.includes('UNIQUE')?409:503});}
}
