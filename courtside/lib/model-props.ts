import type {Game} from './basketball';
export const modelMarkets = {pts:'Points',pr:'Points + rebounds',pra:'Points + rebounds + assists'} as const;
export type ModelMarket = keyof typeof modelMarkets;
export type ModelPrediction = {projection:number;line:number;over:number;under:number};
export type ModelPlayer = {playerId:number;gameId:number;date:string;teamId:number;opponentId:number;home:boolean;name:string;team:string;markets:Record<ModelMarket,ModelPrediction>};
// BALLDONTLIE team IDs, independent of ESPN event IDs.
const teamCodes = ['','ATL','BOS','BKN','CHA','CHI','CLE','DAL','DEN','DET','GSW','HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK','OKC','ORL','PHI','PHX','POR','SAC','SAS','TOR','UTA','WAS'];
const canonical = (code:string) => ({GS:'GSW',NY:'NYK',NO:'NOP',SA:'SAS',UTAH:'UTA',WSH:'WAS'} as Record<string,string>)[code]??code;
// Handle quoted names, commas, escaped quotes, CRLF and a UTF-8 BOM.
export function csvRows(text:string):string[][] {
 const rows:string[][]=[];let row:string[]=[],cell='',quoted=false;
 text=text.replace(/^\uFEFF/,'');
 for(let i=0;i<text.length;i++){const c=text[i];if(c==='"'){if(quoted&&text[i+1]==='"'){cell+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){row.push(cell);cell=''}else if((c==='\n'||c==='\r')&&!quoted){if(c==='\r'&&text[i+1]==='\n')i++;row.push(cell);if(row.some(x=>x.trim()))rows.push(row);row=[];cell=''}else cell+=c}
 if(quoted)throw Error('Prediction CSV has an incomplete quoted field.');
 if(cell||row.length){row.push(cell);rows.push(row)}return rows;
}
export function parseModelProps(text:string){
 const [headers,...rows]=csvRows(text);const required=['player_id','game_id','date','team_id','opponent_id','is_home','player_name','team_name',...Object.keys(modelMarkets).flatMap(k=>[`${k}_projection`,`${k}_line`,`${k}_over_prob`,`${k}_under_prob`])];
 if(!headers||required.some(k=>!headers.includes(k)))throw Error('Prediction CSV is missing required columns.');
 const players:ModelPlayer[]=[];let skipped=0;const seen=new Set<string>();
 for(const values of rows){const r=Object.fromEntries(headers.map((h,i)=>[h,values[i]?.trim()??'']));const number=(k:string)=>r[k]===''?NaN:Number(r[k]);
 const playerId=number('player_id'),gameId=number('game_id'),teamId=number('team_id'),opponentId=number('opponent_id');
 const markets={} as Record<ModelMarket,ModelPrediction>;let valid=true;
 for(const key of Object.keys(modelMarkets) as ModelMarket[]){const p={projection:number(`${key}_projection`),line:number(`${key}_line`),over:number(`${key}_over_prob`),under:number(`${key}_under_prob`)};if(!Object.values(p).every(Number.isFinite)||p.projection<0||p.line<0||p.over<0||p.over>1||p.under<0||p.under>1||Math.abs(p.over+p.under-1)>.001)valid=false;markets[key]=p}
 const identity=`${gameId}:${playerId}`;
 if(!valid||![playerId,gameId,teamId,opponentId].every(x=>Number.isSafeInteger(x)&&x>0)||!teamCodes[teamId]||!teamCodes[opponentId]||teamId===opponentId||!['0','1'].includes(r.is_home)||!/^\d{4}-\d{2}-\d{2}$/.test(r.date)||!Number.isFinite(Date.parse(r.date))||!r.player_name||seen.has(identity)){skipped++;continue}
 seen.add(identity);players.push({playerId,gameId,teamId,opponentId,date:r.date,home:r.is_home==='1',name:r.player_name,team:r.team_name||teamCodes[teamId],markets});
 }
 return {players,skipped};
}
export function matchModelGame(players:ModelPlayer[],game:Game){
 if(!game.start||!Number.isFinite(Date.parse(game.start)))return [];
 const date=new Date(game.start).toLocaleDateString('en-CA',{timeZone:'America/New_York'});
 const home=canonical(game.homeCode),away=canonical(game.awayCode);
 const matched=players.filter(p=>p.date===date&&teamCodes[p.teamId]===(p.home?home:away)&&teamCodes[p.opponentId]===(p.home?away:home));
 // Ambiguous same-day matchups must not mix separate provider events.
 if(new Set(matched.map(p=>p.gameId)).size>1)return [];
 return matched.sort((a,b)=>Number(a.home)-Number(b.home)||a.name.localeCompare(b.name));
}
