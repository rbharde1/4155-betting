import {env} from 'cloudflare:workers';
import type {Game} from './basketball';
import {normalizeProps,practiceProps,gradeProp,type PlayerProp} from './player-props';
async function api(path:string){
 const key=(env as unknown as Record<string,string>).BALLDONTLIE_API_KEY;
 if(!key)throw Error('Live player odds are not connected yet. Try Practice to explore player props.');
 const r=await fetch(`https://api.balldontlie.io${path}`,{headers:{Authorization:key},signal:AbortSignal.timeout(12000)});
 if(!r.ok)throw Error(r.status===401||r.status===403?'Player odds access is unavailable. The provider account needs player-props access.':r.status===429?'Player odds are busy. Please retry shortly.':'Player odds are temporarily unavailable.');
 return await r.json() as any;
}
const code=(s:string)=>({GS:'GSW',NY:'NYK',NO:'NOP',SA:'SAS',UTAH:'UTA'}[s]??s);
export async function playerBoard(game:Game,mode:string){
 const fetchedAt=new Date().toISOString();
 if(mode==='demo')return {props:practiceProps(game),fetchedAt,source:'Practice simulation'};
 if(!game.start||Date.parse(game.start)<=Date.now())throw Error('This game has started. Pregame player picks are closed.');
 const date=new Date(game.start).toLocaleDateString('en-CA',{timeZone:'America/New_York'});
 const schedule=await api(`/v1/games?dates[]=${date}&per_page=100`);
 const matches=schedule.data.filter((x:any)=>code(x.home_team?.abbreviation)===code(game.homeCode)&&code(x.visitor_team?.abbreviation)===code(game.awayCode));
 if(matches.length!==1)throw Error('Player odds are not available for this matchup yet.');
 const id=matches[0].id;const data=await api(`/v2/odds/player_props?game_id=${id}&vendors[]=draftkings`);
 const ids=[...new Set<number>(data.data.map((p:any)=>p.player_id))];
 if(!ids.length)return {props:[],fetchedAt,source:'DraftKings via BALLDONTLIE'};
 const players=await api(`/v1/players?per_page=100&${ids.map(id=>`player_ids[]=${id}`).join('&')}`);
 return {props:normalizeProps(data.data,players.data,id),fetchedAt:new Date().toISOString(),source:'DraftKings via BALLDONTLIE'};
}
export async function propResult(p:PlayerProp,mode:string,side:number){
 if(mode==='demo'){const value=Math.max(0,Math.floor(p.line)+(p.playerId%3)-1);return {result:gradeProp(value,p.line,side),score:`${value} ${p.stat} (simulated)`}}
 const game=await api(`/v1/games/${p.providerGameId}`);if(game.data?.status!=='Final')return null;
 const stats=await api(`/v1/stats?game_ids[]=${p.providerGameId}&player_ids[]=${p.playerId}&per_page=100`);
 const row=stats.data.find((x:any)=>x.player?.id===p.playerId&&x.game?.id===p.providerGameId);
 if(!row||row.min==null||row.min==='')return null;
 if(/^0(?::00)?$/.test(String(row.min)))return {result:'void',score:'Did not play'};
 const value=row[{points:'pts',assists:'ast',rebounds:'reb'}[p.stat]];
 if(!Number.isInteger(value)||value<0)return null;
 return {result:gradeProp(value,p.line,side),score:`${value} ${p.stat}`};
}
