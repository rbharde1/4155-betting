'use client';
import {X,ArrowRight,Layers} from 'lucide-react';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {signed} from '@/lib/basketball';
import {americanOdds,combinedDecimal,parlayProfitCents} from '@/lib/parlay';
import {selectionQuote,type Selection} from '@/lib/slip';
export type {Selection} from '@/lib/slip';
const points=(n:number)=>n.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
export default function ParlaySlip({legs,stake,setStake,balance,busy,disabled,validStake,issue,remove,submit}:{legs:Selection[];stake:string;setStake:(s:string)=>void;balance:number;busy:boolean;disabled:boolean;validStake:boolean;issue:string;remove:(id:string)=>void;submit:()=>void}){
 const odds=legs.map(l=>selectionQuote(l).odds),decimal=combinedDecimal(odds),amount=Number(stake),profit=validStake?parlayProfitCents(Math.round(amount*100),odds)/100:0;
 return <form className="slip-form" onSubmit={e=>{e.preventDefault();submit()}}>
 <div className="parlay-intro"><Layers size={17}/><div><strong>One ticket. All your picks.</strong><p>One pick is a single. Add another for a parlay.</p></div></div>
 {!legs.length&&<div className="parlay-empty">Choose a game line or player prop to start.</div>}
 {legs.map((l,i)=>{const q=selectionQuote(l);return <div className="slip-selection parlay-leg" key={l.id}><span className="leg-number">{i+1}</span><div><small>{l.market.toUpperCase()}</small><h3>{q.label} <span>{signed(q.odds)}</span></h3><p>{l.game.awayCode} at {l.game.homeCode}</p></div><Button type="button" variant="ghost" size="icon-sm" aria-label={`Remove ${q.label}`} disabled={busy} onClick={()=>remove(l.id)}><X size={14}/></Button></div>})}
 {!!legs.length&&<><div className="combined-odds"><span>{legs.length===1?'Odds':'Combined odds'}</span><strong>{signed(americanOdds(decimal))}<small>{decimal.toFixed(3)} decimal</small></strong></div><label htmlFor="parlay-stake">PAPER STAKE <span>Up to your available balance</span></label><div className="stake-input"><Input id="parlay-stake" inputMode="decimal" type="number" min="1" max={balance} step="0.01" value={stake} disabled={busy} onChange={e=>setStake(e.target.value)} required/><span>P</span></div><div className="stake-presets">{[1,2,5,10].map(n=><Button type="button" size="sm" variant={amount===n?'secondary':'outline'} key={n} disabled={busy} onClick={()=>setStake(String(n))}>{n} P</Button>)}</div><div className="slip-calculation"><p>Potential profit <strong>+{points(profit)} P</strong></p><p>Total return <b>{points(validStake?amount+profit:0)} P</b></p></div></>}
 {issue&&<p className="validation">{issue}</p>}
 <Button type="submit" className="lock-button" disabled={disabled||!legs.length}>{busy?'Locking pick…':!legs.length?'Select a pick':legs.length===1?'Lock single pick':`Lock ${legs.length}-leg parlay`}<ArrowRight size={16}/></Button>
 <p className="irreversible-note">All legs must win. A push or void removes that leg and adjusts the return. Locked tickets cannot be edited.</p><p className="parlay-pricing">Parlay returns multiply individual odds, including same-game picks. Correlations are not priced; these are paper payouts, not sportsbook quotes.</p>
 </form>
}
