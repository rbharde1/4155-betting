type TeamLeg={gameId:string;market:string;side:number;kind?:string};
export function preferSpread<T extends TeamLeg>(legs:T[]):T[]{
 return legs.filter(leg=>leg.kind||leg.market!=='moneyline'||!legs.some(other=>!other.kind&&other.market==='spread'&&other.gameId===leg.gameId&&other.side===leg.side));
}

export function ticketType(legs:{gameId:string}[]){
 if(!legs.length)return 'Your pick slip';
 if(legs.length===1)return 'Single';
 return new Set(legs.map(l=>l.gameId)).size===1?'SGP':'SGPx';
}
