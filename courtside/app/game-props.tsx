'use client';
import {useEffect,useState} from 'react';
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription} from '@/components/ui/dialog';
import {Button} from '@/components/ui/button';
import {Tabs,TabsList,TabsTrigger} from '@/components/ui/tabs';
import {Game,signed} from '@/lib/basketball';
import {propStats,type PlayerProp,type PropStat} from '@/lib/player-props';
import {type Selection} from '@/lib/slip';
import ModelProps from './model-props';
export default function GameProps({game,mode,ready,busy,onClose,legs,onSelect}:{game:Game;mode:string;ready:boolean;busy:boolean;onClose:()=>void;legs:Selection[];onSelect:(s:Selection)=>void}){
 const [sourceView,setSourceView]=useState('model');
 const [stat,setStat]=useState<PropStat>('points'),[rows,setRows]=useState<PlayerProp[]>([]),[error,setError]=useState(''),[loading,setLoading]=useState(true),[refresh,setRefresh]=useState(0),[stamp,setStamp]=useState(''),[source,setSource]=useState('');
 const [now,setNow]=useState(Date.now());
 useEffect(()=>{if(sourceView!=='markets')return;const c=new AbortController();setLoading(true);setError('');fetch(`/api/player-props?mode=${mode}&gameId=${encodeURIComponent(game.id)}`,{signal:c.signal}).then(async r=>{const d:any=await r.json();if(!r.ok)throw Error(d.error);return d}).then(d=>{setRows(d.props);setStamp(d.fetchedAt);setSource(d.source)}).catch(e=>{if(!c.signal.aborted){setError(e.message);setRows([])}}).finally(()=>{if(!c.signal.aborted)setLoading(false)});return()=>c.abort()},[game.id,mode,refresh,sourceView]);
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),5000);return()=>clearInterval(timer)},[]);
 const locked=mode==='live'&&(!game.start||Date.parse(game.start)<=now||!stamp||now-Date.parse(stamp)>120000);
 return <Dialog open onOpenChange={open=>{if(!open&&!busy)onClose()}}><DialogContent className="player-props-dialog" showCloseButton={!busy}><DialogHeader><div className="eyebrow">PLAYER PROPS · PAPER ONLY</div><DialogTitle>{game.awayCode} at {game.homeCode}</DialogTitle><DialogDescription>{game.away} vs. {game.home} · {game.time} ET</DialogDescription></DialogHeader>
 <Button type="button" disabled={busy} onClick={onClose}>Review pick slip · {legs.length} {legs.length===1?'pick':'picks'}</Button>
 <Tabs value={sourceView} onValueChange={v=>{if(!busy){setSourceView(v);}}}><TabsList className="prop-tabs"><TabsTrigger value="model" disabled={busy}>Model predictions</TabsTrigger><TabsTrigger value="markets" disabled={busy}>Paper markets</TabsTrigger></TabsList></Tabs>
 {sourceView==='model'?<ModelProps game={game} mode={mode} ready={ready} busy={busy} legs={legs} onSelect={onSelect}/>:<>
 <Tabs value={stat} onValueChange={s=>setStat(s as PropStat)}><TabsList className="prop-tabs">{propStats.map(s=><TabsTrigger key={s} value={s}>{s[0].toUpperCase()+s.slice(1)}</TabsTrigger>)}</TabsList></Tabs>
 <div className="prop-source"><span>{source}{stamp&&` · Retrieved ${new Date(stamp).toLocaleTimeString()}`}</span><Button variant="outline" size="sm" disabled={loading||busy} onClick={()=>setRefresh(n=>n+1)}>Refresh odds</Button></div>
 {loading?<p role="status">Loading player odds…</p>:error?<div className="error-state" role="alert">{error}</div>:!rows.some(p=>p.stat===stat)?<div className="empty-panel"><h3>No {stat} lines available yet.</h3><p>Check again when the sportsbook posts player odds.</p></div>:<div className="prop-list"><div className="prop-row prop-labels"><span>PLAYER · {stat.toUpperCase()}</span><span>OVER</span><span>UNDER</span></div>{rows.filter(p=>p.stat===stat).map(p=><div className="prop-row" key={p.id}><div><strong>{p.player}</strong><small>{p.team}</small></div>{[0,1].map(side=><Button key={side} variant="outline" className={'odds-button '+(legs.some(l=>l.kind==='player'&&l.game.id===game.id&&l.propId===p.id&&l.side===side)?'selected':'')} aria-label={`${p.player} ${side===0?'over':'under'} ${p.line} ${p.stat} at ${signed(side===0?p.over:p.under)}`} aria-pressed={legs.some(l=>l.kind==='player'&&l.game.id===game.id&&l.propId===p.id&&l.side===side)} disabled={busy||locked||!ready} onClick={()=>onSelect({kind:'player',game,market:p.stat,side,id:crypto.randomUUID(),playerId:p.playerId,propId:p.id,label:`${p.player} · ${side===0?'Over':'Under'} ${p.line} ${p.stat}`,point:p.line,odds:side===0?p.over:p.under})}><span>{side===0?'O':'U'} {p.line}</span><small>{signed(side===0?p.over:p.under)}</small></Button>)}</div>)}</div>}
 {locked&&!loading&&!error&&<p role="status">Odds expired or the game started. Refresh for available lines.</p>}

 <p className="record-note">Add game lines and player props to the same slip. Only one side per player and stat is allowed. Includes overtime; exact ties refund the stake. Confirmed non-participation voids the pick. Unconfirmed stats stay pending. Locked picks cannot be changed.</p>
 </>}

 </DialogContent></Dialog>
}
