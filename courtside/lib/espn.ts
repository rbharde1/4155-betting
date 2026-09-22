import {Game} from './basketball';
export const ODDS_URL='https://www.espn.com/nba/odds';
function extractState(html:string){
 const match=/window\[['"]__espnfitt__['"]\]\s*=\s*/.exec(html);if(!match)throw new Error('ESPN odds format changed.');
 const start=match.index+match[0].length;let depth=0,quoted=false,escaped=false;
 for(let i=start;i<html.length;i++){const c=html[i];if(quoted){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c==='"')quoted=false;}else if(c==='"')quoted=true;else if(c==='{')depth++;else if(c==='}'&&--depth===0)return JSON.parse(html.slice(start,i+1));}
 throw new Error('Incomplete ESPN response.');
}
const colors:Record<string,string>={BOS:'#58ba8c',LAL:'#c69de7',GS:'#f0cc6a',NY:'#ef9f60',DET:'#7eb3ed',OKC:'#7bc5ec',SA:'#c1cbd1',PHI:'#809fe7',MIL:'#85b8a0',CLE:'#d28799',DEN:'#eac97c'};
function number(s:unknown){if(typeof s!=='string'&&typeof s!=='number')return NaN;const text=String(s).replace('−','-');return /^[+-]?\d+(\.\d+)?$/.test(text)?Number(text):NaN;}
export function parseOdds(html:string,fetchedAt=new Date().toISOString()):Game[]{
 const content=extractState(html)?.page?.content?.odds;
 if(!Array.isArray(content?.odds))throw new Error('ESPN odds are unavailable.');
 const result:Game[]=[];
 for(const group of content.odds)for(const section of group.sections??[])for(const g of section.games??[]){
 const [a,h]=g.odds??[];const start=g.date;
 if(!a||!h||g.isLiveState||!g.timeValid||!Number.isFinite(Date.parse(start))||Date.parse(start)<=Date.now())continue;
 const spread=number(h.pointSpread?.primary), awaySpread=number(a.pointSpread?.primary), total=number(a.total?.primary?.replace(/^[ou]/i,'')),homeTotal=number(h.total?.primary?.replace(/^[ou]/i,''));
 const awayOdds=number(a.moneyline?.primary),homeOdds=number(h.moneyline?.primary);
 const prices=[number(a.pointSpread?.secondary),number(h.pointSpread?.secondary),number(a.total?.secondary),number(h.total?.secondary)];
 if(![spread,awaySpread,total,homeTotal,awayOdds,homeOdds,...prices].every(Number.isFinite)||spread!==-awaySpread||total!==homeTotal||[awayOdds,homeOdds,...prices].some(x=>Math.abs(x)<100)||total<=0)continue;
 const awayCode=a.line?.primaryText,homeCode=h.line?.primaryText;
 if(!/^\d+$/.test(String(g.gameInfo?.gameId))||!awayCode||!homeCode)continue;
 result.push({id:String(g.gameInfo.gameId),away:a.line.primaryTextFullWide,home:h.line.primaryTextFullWide,awayCode,homeCode,awayColor:colors[awayCode]??'#a2c4b1',homeColor:colors[homeCode]??'#c7b29a',time:new Date(start).toLocaleTimeString('en-US',{timeZone:'America/New_York',hour:'numeric',minute:'2-digit'}),start,spread,total,awayOdds,homeOdds,prices,source:`${g.providerName??content.providerName??'Sportsbook'} via ESPN`,fetchedAt});
 }
 return result.sort((a,b)=>Date.parse(a.start!)-Date.parse(b.start!));
}
let cached:{games:Game[];fetchedAt:string;expires:number}|undefined;
export async function liveBoard(force=false){
 if(!force&&cached&&cached.expires>Date.now())return cached;
 const response=await fetch(ODDS_URL,{headers:{'Accept':'text/html','User-Agent':'CourtsidePaperPicks/1.0'},signal:AbortSignal.timeout(12000)});
 if(!response.ok)throw new Error('The odds source is unavailable. Please try again.');
 const fetchedAt=new Date().toISOString();const games=parseOdds(await response.text(),fetchedAt);
 cached={games,fetchedAt,expires:Date.now()+60000};return cached;
}
export async function finalScore(id:string){
 if(!/^\d+$/.test(id))return null;
 const r=await fetch(`https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event=${id}`,{signal:AbortSignal.timeout(8000)});
 if(!r.ok)return null;const d:any=await r.json();const c=d.header?.competitions?.[0];if(!c||String(c.id)!==id)return null;
 if(['STATUS_CANCELED','STATUS_CANCELLED'].includes(c.status?.type?.name))return {void:true,away:0,home:0};
 if(c.status?.type?.completed!==true||c.status?.type?.name!=='STATUS_FINAL')return null;
 const a=c.competitors?.find((x:any)=>x.homeAway==='away'),h=c.competitors?.find((x:any)=>x.homeAway==='home');
 if(a?.score==null||h?.score==null)return null;const away=Number(a.score),home=Number(h.score);if(!Number.isInteger(away)||!Number.isInteger(home)||away<0||home<0)return null;
 return {void:false,away,home};
}
