import {competitionWeek} from '@/lib/weekly';
import csv from '@/ml/data/processed/nba_prop_predictions.csv?raw';
import {parseModelProps,matchModelGame} from '@/lib/model-props';
import {db,user,state,sameOrigin} from '@/lib/store';
import {profit} from '@/lib/basketball';
import {modelMarkets,type ModelMarket} from '@/lib/model-props';
import {liveBoard} from '@/lib/espn';
export const dynamic='force-dynamic';
let parsed:ReturnType<typeof parseModelProps>|undefined;
export async function GET(request:Request){
 try{
 const id=new URL(request.url).searchParams.get('gameId');
 const game=(await liveBoard()).games.find(g=>g.id===id);
 if(!game)return Response.json({error:'This matchup is no longer on the pregame board. Refresh the game board.'},{status:404});
 parsed??=parseModelProps(csv);const dates=parsed.players.map(p=>p.date).sort();
 return Response.json({players:matchModelGame(parsed.players,game),coverage:{from:dates[0]??null,to:dates.at(-1)??null},skipped:parsed.skipped,source:'Team regression models · CSV snapshot'},{headers:{'Cache-Control':'no-store'}});
 }catch{return Response.json({error:'Model predictions could not be loaded. Please retry.'},{status:503})}
}

export async function POST(request:Request){
 if(!sameOrigin(request))return Response.json({error:'Invalid request origin.'},{status:403});
 try{
 const owner=await user();const b:any=await request.json();
 if(b.mode!=='live'||!['pts','pr','pra'].includes(b.market)||![0,1].includes(b.side)||typeof b.id!=='string'||!/^[\w-]{16,64}$/.test(b.id)||typeof b.stake!=='number'||!Number.isFinite(b.stake)||b.stake<1||Math.abs(b.stake*100-Math.round(b.stake*100))>0.00001)return Response.json({error:'Choose a valid market and a stake of at least 1 point, with at most two decimals.'},{status:400});
 const prior=await db().prepare('SELECT id FROM picks WHERE id=? AND owner=? AND mode=?').bind(b.id,owner,'live').first();if(prior)return Response.json(await state('live',owner));
 const game=(await liveBoard()).games.find(g=>g.id===b.gameId);
 if(!game?.start||!Number.isFinite(Date.parse(game.start))||Date.parse(game.start)<=Date.now())return Response.json({error:'This game is no longer open for pregame picks.'},{status:409});
 parsed??=parseModelProps(csv);const player=matchModelGame(parsed.players,game).find(p=>p.playerId===b.playerId);
 const market=b.market as ModelMarket;const prediction=player?.markets[market];
 if(!player||!prediction||prediction.line!==b.line||b.odds!==-110)return Response.json({error:'The generated line changed or is unavailable. Refresh and select it again.'},{status:409});
 const now=new Date().toISOString(),stake=Math.round(b.stake*100);
 const snapshot={kind:'model',eventId:game.id,playerId:player.playerId,providerGameId:player.gameId,name:player.name,home:player.home,market,line:prediction.line,projection:prediction.projection,overProbability:prediction.over,underProbability:prediction.under};
 const week=competitionWeek(new Date(now));
 const result=await db().prepare("INSERT INTO picks (id,owner,game_id,mode,market,side,label,matchup,odds,point,stake_cents,profit_cents,result,source,fetched_at,start,created_at,player_prop) SELECT ?,?,?,'live',?,?,?,?,?,?,?,?,'pending',?,?,?,?,? WHERE ? <= 10000 + COALESCE((SELECT SUM(CASE WHEN result='pending' THEN -stake_cents WHEN result='won' THEN profit_cents WHEN result='lost' THEN -stake_cents ELSE 0 END) FROM picks WHERE owner=? AND mode='live' AND created_at>=? AND created_at<?),0)").bind(b.id,owner,`model:${game.id}:${player.playerId}`,market,b.side,`${player.name} · ${b.side===0?'Over':'Under'} ${prediction.line} ${market.toUpperCase()}`,`${game.away} at ${game.home}`,-110,prediction.line,stake,Math.round(profit(b.stake,-110)*100),'CSV model line · Courtside paper odds -110',now,game.start,now,JSON.stringify(snapshot),stake,owner,week.start,week.end).run();
 if(!result.meta.changes)return Response.json({error:'Not enough paper points available.'},{status:409});
 return Response.json(await state('live',owner),{status:201});
 }catch(e){const message=(e as Error).message;return Response.json({error:message.includes('UNIQUE')?'You already picked this player and model market for this game.':message.includes('Sign in')?message:'Could not save your pick. Your selection is kept; please retry.'},{status:message.includes('UNIQUE')?409:503})}
}
