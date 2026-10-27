'use client';
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {type Game} from '@/lib/basketball';
import {type Selection} from '@/lib/slip';
import ModelProps from './model-props';
export default function GameProps({game,mode,ready,busy,onClose,legs,onSelect}:{game:Game;mode:string;ready:boolean;busy:boolean;onClose:()=>void;legs:Selection[];onSelect:(s:Selection)=>void}){
 return <Dialog open onOpenChange={open=>{if(!open&&!busy)onClose()}}><DialogContent className="player-props-dialog" showCloseButton={!busy}><DialogHeader><div className="eyebrow">PLAYER PROPS · PAPER ONLY</div><DialogTitle>{game.awayCode} at {game.homeCode}</DialogTitle><DialogDescription>{game.away} vs. {game.home} · {game.time} ET</DialogDescription></DialogHeader>
 <Button type="button" disabled={busy} onClick={onClose}>Review pick slip · {legs.length} {legs.length===1?'pick':'picks'}</Button>
 <ModelProps game={game} mode={mode} ready={ready} busy={busy} legs={legs} onSelect={onSelect}/>
 </DialogContent></Dialog>
}
