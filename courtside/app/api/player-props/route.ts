import {games,profit} from '@/lib/basketball';
import {liveBoard} from '@/lib/espn';
import {playerBoard} from '@/lib/bdl';
import {db,user,state,sameOrigin} from '@/lib/store';
export const dynamic='force-dynamic';
async function board(mode:string,id:string){const game=(mode==='demo'?games:(await liveBoard()).games).find(g=>g.id===id);if(!game)throw Error('This game is no longer available for pregame picks.');return {game,...await playerBoard(game,mode)}}
export async function GET(request:Request){try{const q=new URL(request.url).searchParams;return Response.json(await board(q.get('mode')==='demo'?'demo':'live',q.get('gameId')??''),{headers:{'Cache-Control':'no-store'}})}catch(e){return Response.json({error:(e as Error).message},{status:503,headers:{'Cache-Control':'no-store'}})}}
export async function POST(request:Request){
 if(!sameOrigin(request))return Response.json({error:'Invalid request origin.'},{status:403});
 try{const owner=await user();const b:any=await request.json();
 if(!['demo','live'].includes(b.mode)||![0,1].includes(b.side)||typeof b.id!=='string'||!/^[\w-]{16,64}$/.test(b.id)||typeof b.stake!=='number'||!Number.isFinite(b.stake)||b.stake<1||b.stake>1000||Math.abs(b.stake*100-Math.round(b.stake*100))>0.00001)return Response.json({error:'Enter a valid pick and stake from 1 to 1,000 paper points, with at most two decimals.'},{status:400});
 const prior=await db().prepare('SELECT id FROM picks WHERE id=? AND owner=? AND mode=?').bind(b.id,owner,b.mode).first();if(prior)return Response.json(await state(b.mode,owner));
 const data=await board(b.mode,b.gameId);const p=data.props.find(p=>p.id===b.propId);if(!p||p.line!==b.line||(b.side===0?p.over:p.under)!==b.odds)return Response.json({error:'This player line changed or is unavailable. Refresh and select it again.'},{status:409});
 if(b.mode==='live'&&(!data.game.start||Date.parse(data.game.start)<=Date.now()))return Response.json({error:'The game has started. Player picks are locked.'},{status:409});
 const odds=b.side===0?p.over:p.under,stake=Math.round(b.stake*100),now=new Date().toISOString();
 const inserted=await db().prepare("INSERT INTO picks (id,owner,game_id,mode,market,side,label,matchup,odds,point,stake_cents,profit_cents,result,source,fetched_at,start,created_at,player_prop) SELECT ?,?,?,?,?,?,?,?,?,?,?,?,'pending',?,?,?,?,? WHERE ? <= 100000 + COALESCE((SELECT SUM(CASE WHEN result='pending' THEN -stake_cents WHEN result='won' THEN profit_cents WHEN result='lost' THEN -stake_cents ELSE 0 END) FROM picks WHERE owner=? AND mode=?),0)").bind(b.id,owner,`prop:${data.game.id}:${p.playerId}`,b.mode,p.stat,b.side,`${p.player} · ${b.side===0?'Over':'Under'} ${p.line} ${p.stat}`,`${data.game.away} at ${data.game.home}`,odds,p.line,stake,Math.round(profit(b.stake,odds)*100),data.source,data.fetchedAt,data.game.start??now,now,JSON.stringify(p),stake,owner,b.mode).run();
 if(!inserted.meta.changes)return Response.json({error:'Not enough paper points available.'},{status:409});
 return Response.json(await state(b.mode,owner),{status:201});
 }catch(e){const m=(e as Error).message;return Response.json({error:m.includes('UNIQUE')?'You already picked this player’s stat for this game.':m.includes('D1')?'Could not save your pick. Please retry.':m},{status:m.includes('UNIQUE')?409:503})}
}
