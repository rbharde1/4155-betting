import type {ModelMarket} from './model-props';
export type ModelTicket={kind:'model';eventId:string;playerId:number;providerGameId:number;name:string;home:boolean;market:ModelMarket;line:number;projection:number;overProbability:number;underProbability:number};
const normalize=(name:string)=>name.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
export function gradeModelTicket(data:any,ticket:ModelTicket,side:number){
 const c=data.header?.competitions?.[0];if(!c||String(c.id)!==ticket.eventId)return null;
 if(['STATUS_CANCELED','STATUS_CANCELLED'].includes(c.status?.type?.name))return {result:'void',score:'Cancelled'};
 if(c.status?.type?.name!=='STATUS_FINAL'||c.status?.type?.completed!==true)return null;
 const team=c.competitors?.find((x:any)=>x.homeAway===(ticket.home?'home':'away'));
 const box=data.boxscore?.players?.find((x:any)=>String(x.team?.id)===String(team?.id));if(!team||!box)return null;
 const matches=(box.statistics??[]).flatMap((group:any)=>(group.athletes??[]).filter((a:any)=>normalize(a.athlete?.displayName??'')===normalize(ticket.name)).map((a:any)=>({a,labels:group.labels})));
 if(matches.length!==1)return null;const {a,labels}=matches[0];
 if(a.didNotPlay===true)return {result:'void',score:'Did not play'};
 if(!Array.isArray(labels)||!Array.isArray(a.stats))return null;
 const required=ticket.market==='pts'?['PTS']:ticket.market==='pr'?['PTS','REB']:['PTS','REB','AST'];
 const values=required.map(k=>{const raw=a.stats[labels.indexOf(k)];return typeof raw==='string'&&/^\d+$/.test(raw)?Number(raw):NaN});
 if(!values.every(Number.isInteger))return null;
 const value=values.reduce((s:number,n:number)=>s+n,0);
 return {result:value===ticket.line?'push':(side===0?value>ticket.line:value<ticket.line)?'won':'lost',score:`${value} ${ticket.market.toUpperCase()} · ESPN final`};
}
export async function fetchModelResult(eventId:string){
 if(!/^\d+$/.test(eventId))return null;
 const r=await fetch(`https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=${eventId}`,{signal:AbortSignal.timeout(8000)});
 return r.ok?await r.json():null;
}
