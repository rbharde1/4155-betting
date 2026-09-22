export type LegResult='pending'|'won'|'lost'|'push'|'void';
export type ParlayLeg={gameId:string;market:string;side:number;label:string;matchup:string;odds:number;point:number|null;source:string;fetchedAt:string;start:string;result:LegResult;score?:string};
export const decimalOdds=(odds:number)=>1+(odds>0?odds/100:100/-odds);
export const combinedDecimal=(odds:number[])=>odds.reduce((p,n)=>p*decimalOdds(n),1);
export function americanOdds(decimal:number){return decimal<=1?0:Math.round(decimal>=2?(decimal-1)*100:-100/(decimal-1));}
export function parlayProfitCents(stakeCents:number,odds:number[]){return Math.round(stakeCents*(combinedDecimal(odds)-1));}
export function gradeParlay(stakeCents:number,legs:Pick<ParlayLeg,'odds'|'result'>[]){
 if(legs.some(l=>l.result==='lost'))return {result:'lost' as LegResult,profitCents:0};
 if(legs.some(l=>l.result==='pending'))return {result:'pending' as LegResult,profitCents:parlayProfitCents(stakeCents,legs.filter(l=>l.result!=='push'&&l.result!=='void').map(l=>l.odds))};
 const winners=legs.filter(l=>l.result==='won');
 return winners.length?{result:'won' as LegResult,profitCents:parlayProfitCents(stakeCents,winners.map(l=>l.odds))}:{result:'push' as LegResult,profitCents:0};
}
