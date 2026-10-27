import {type Game,type Market,quote} from './basketball';
export type Selection={game:Game;market:string;side:number;id:string;kind?:'model'|'player';playerId?:number;propId?:string;label?:string;odds?:number;point?:number};
export function selectionQuote(l:Selection){return l.kind?{label:l.label!,odds:l.odds!,point:l.point!}:quote(l.game,l.market as Market,l.side)}
export function marketKey(l:{gameId:string;market:string;kind?:string;playerId?:number}){return l.kind?`${l.gameId}:player:${l.playerId}:${({points:'pts',assists:'ast',rebounds:'reb'} as Record<string,string>)[l.market]??l.market}`:`${l.gameId}:team:${l.market}`}
export const selectionKey=(l:Selection)=>marketKey({...l,gameId:l.game.id});
export function ticketLeg(l:Selection){return {gameId:l.game.id,market:l.market,side:l.side,kind:l.kind,playerId:l.playerId,propId:l.propId,...selectionQuote(l)}}
