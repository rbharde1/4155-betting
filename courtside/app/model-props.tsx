'use client';
import {useEffect,useState} from 'react';
import {type Game,teamLogo} from '@/lib/basketball';
import {type Selection} from '@/lib/slip';
import {modelMarkets,type ModelMarket,type ModelPlayer} from '@/lib/model-props';
import {Button} from '@/components/ui/button';
import {Tabs,TabsList,TabsTrigger} from '@/components/ui/tabs';
export default function ModelProps({game,mode,ready,busy,legs,onSelect}:{game:Game;mode:string;ready:boolean;busy:boolean;legs:Selection[];onSelect:(s:Selection)=>void}){
 const [now,setNow]=useState(Date.now());useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer)},[]);
 const locked=!game.start||Date.parse(game.start)<=now;
 const selected=(p:ModelPlayer,market:ModelMarket,side:number)=>legs.some(l=>l.kind==='model'&&l.game.id===game.id&&l.playerId===p.playerId&&l.market===market&&l.side===side);
 function choose(p:ModelPlayer,market:ModelMarket,side:number){onSelect({kind:'model',game,playerId:p.playerId,market,side,id:crypto.randomUUID(),label:`${p.name} · ${side===0?'Over':'Under'} ${p.markets[market].line} ${market.toUpperCase()}`,odds:-110,point:p.markets[market].line})}
 const [market,setMarket]=useState<ModelMarket>('pts'),[players,setPlayers]=useState<ModelPlayer[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[revision,setRevision]=useState(0),[coverage,setCoverage]=useState<{from:string|null;to:string|null}|null>(null);
 useEffect(()=>{const abort=new AbortController();setPlayers([]);setError('');setCoverage(null);setLoading(true);
 fetch(`/api/model-props?gameId=${encodeURIComponent(game.id)}`,{signal:abort.signal}).then(async r=>{const d:any=await r.json();if(!r.ok)throw Error(d.error);return d}).then(d=>{if(!abort.signal.aborted){setPlayers(d.players);setCoverage(d.coverage)}}).catch(e=>{if(!abort.signal.aborted)setError(e.message)}).finally(()=>{if(!abort.signal.aborted)setLoading(false)});return()=>abort.abort()
 },[game.id,mode,revision]);
 return <section aria-label="Model player predictions">
 <Tabs value={market} onValueChange={v=>setMarket(v as ModelMarket)}><TabsList className="prop-tabs">{(Object.keys(modelMarkets) as ModelMarket[]).map(k=><TabsTrigger value={k} key={k}>{k.toUpperCase()}</TabsTrigger>)}</TabsList></Tabs>
 <div className="prop-source"><Button size="sm" variant="outline" disabled={loading||busy} onClick={()=>setRevision(v=>v+1)}>Refresh predictions</Button></div>

 {loading?<p role="status">Loading model predictions…</p>:error?<p role="alert" className="error-state">{error}</p>:!players.length?<div className="empty-panel"><h3>No model predictions for this matchup yet.</h3><p>The CSV must contain this game’s date and both teams. Predictions from other games are not reused.</p></div>:<div className="model-table-wrap"><table className="model-table"><caption>{modelMarkets[market]} predictions · {players.length} players</caption><thead><tr><th>Player</th><th>Projection</th><th>Model line</th><th>Over</th><th>Under</th></tr></thead><tbody>{[...players].sort((a,b)=>b.markets[market].projection-a.markets[market].projection||a.name.localeCompare(b.name)).map(p=>{const v=p.markets[market];return <tr key={`${p.gameId}:${p.playerId}`}><th scope="row"><span className="model-player-name"><PlayerTeamLogo code={p.home?game.homeCode:game.awayCode} name={p.team}/><span>{p.name}</span></span></th><td>{v.projection.toFixed(1)}</td><td>{v.line.toFixed(1)}</td>{[0,1].map(side=><td key={side}><Button variant="outline" className={selected(p,market,side)?'selected':''} aria-label={`${p.name} ${side===0?'Over':'Under'} ${v.line} ${market.toUpperCase()} at -110`} aria-pressed={selected(p,market,side)} disabled={busy||locked||!ready} onClick={()=>choose(p,market,side)}>{side===0?'Over':'Under'} {v.line} · -110</Button><small>{((side===0?v.over:v.under)*100).toFixed(1)}% model estimate</small></td>)}</tr>})}</tbody></table></div>}

 </section>
}

function PlayerTeamLogo({code,name}:{code:string;name:string}){
 const [failed,setFailed]=useState(false);
 return failed?<span className="model-player-logo-fallback" role="img" aria-label={name}>{code}</span>:<img className="model-player-logo" src={teamLogo(code)} alt={name} title={name} width={28} height={28} loading="lazy" onError={()=>setFailed(true)}/>;
}
