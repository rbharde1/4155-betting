'use client';
import {X,ArrowRight,Layers} from 'lucide-react';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {Game,Market,quote,signed} from '@/lib/basketball';
import {americanOdds,combinedDecimal,parlayProfitCents} from '@/lib/parlay';
export type Selection={game:Game;market:Market;side:number;id:string};
const points=(n:number)=>n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
export default function ParlaySlip({legs,stake,setStake,balance,busy,disabled,validStake,issue,remove,submit}:{legs:Selection[];stake:string;setStake:(s:string)=>void;balance:number;busy:boolean;disabled:boolean;validStake:boolean;issue:string;remove:(id:string)=>void;submit:()=>void}){
 const odds=legs.map(l=>quote(l.game,l.market,l.side).odds),decimal=combinedDecimal(odds),amount=Number(stake),profit=validStake?parlayProfitCents(Math.round(amount*100),odds)/100:0;
 return <form className="slip-form" onSubmit={e=>{e.preventDefault();submit()}}>
 <div className="parlay-intro"><Layers size={17}/><div><strong>One ticket. All your picks.</strong><p>Combine 2–6 different games.</p></div></div>
 {!legs.length&&<div className="parlay-empty">Tap a moneyline, spread, or total to add your first leg.</div>}
 {legs.map((l,i)=>{const q=quote(l.game,l.market,l.side);return <div className="slip-selection parlay-leg" key={l.id}><span className="leg-number">{i+1}</span><div><small>{l.market.toUpperCase()}</small><h3>{q.label} <span>{signed(q.odds)}</span></h3><p>{l.game.awayCode} at {l.game.homeCode}</p></div><Button type="button" variant="ghost" size="icon-sm" aria-label={`Remove ${q.label}`} disabled={busy} onClick={()=>remove(l.id)}><X size={14}/></Button></div>})}
 {!!legs.length&&<><div className="combined-odds"><span>Combined odds</span><strong>{signed(americanOdds(decimal))}<small>{decimal.toFixed(3)} decimal</small></strong></div><label htmlFor="parlay-stake">PAPER STAKE <span>One stake for all legs</span></label><div className="stake-input"><Input id="parlay-stake" inputMode="decimal" type="number" min="1" max={Math.min(1000,balance)} step="0.01" value={stake} disabled={busy} onChange={e=>setStake(e.target.value)} required/><span>P</span></div><div className="stake-presets">{[10,25,50,100].map(n=><Button type="button" size="sm" variant={amount===n?'secondary':'outline'} key={n} disabled={busy} onClick={()=>setStake(String(n))}>{n} P</Button>)}</div><div className="slip-calculation"><p>Potential profit <strong>+{points(profit)} P</strong></p><p>Total return <b>{points(validStake?amount+profit:0)} P</b></p></div></>}
 {issue&&<p className="validation">{issue}</p>}
 <Button type="submit" className="lock-button" disabled={disabled||legs.length<2}>{busy?'Locking parlay…':legs.length<2?`Add ${2-legs.length} more ${legs.length?'leg':'legs'}`:`Lock ${legs.length}-leg parlay`}<ArrowRight size={16}/></Button>
 <p className="irreversible-note">All legs must win. A push or void removes that leg and adjusts the return. Locked tickets cannot be edited.</p><p className="parlay-pricing">Courtside calculates paper parlay odds from individual lines. This is not a sportsbook parlay quote.</p>
 </form>
}
