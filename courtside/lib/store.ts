import {gradeParlay,ParlayLeg} from './parlay';
import {resultFor} from './grading';
import {env} from 'cloudflare:workers';
import {headers} from 'next/headers';
import {finalScore} from './espn';
export function db(){if(!env.DB)throw new Error('Prediction storage is temporarily unavailable.');return env.DB;}
export async function user(){const id=(await headers()).get('oai-authenticated-user-id');if(!id)throw new Error('Sign in to save paper picks.');return id;}
export function sameOrigin(request:Request){const origin=request.headers.get('origin');return !origin||origin===new URL(request.url).origin;}

export async function settle(mode:string,owner:string){
 const pending=await db().prepare("SELECT * FROM picks WHERE owner=? AND mode=? AND (result='pending' OR (market='parlay' AND result='lost' AND legs LIKE '%\"result\":\"pending\"%')) ORDER BY created_at LIMIT 100").bind(owner,mode).all<any>();let count=0;
 const scores=new Map<string,Awaited<ReturnType<typeof finalScore>>>();
 async function getScore(id:string,start:string){
  if(mode==='live'&&Date.parse(start)>Date.now())return null;
  if(scores.has(id))return scores.get(id)!;
  let score=null;try{score=mode==='demo'?{void:false,away:108+(id.length%12),home:104+(id.charCodeAt(6)%18)}:await finalScore(id);}catch{/* Keep unavailable results pending. */}
  scores.set(id,score);return score;
 }
 for(const p of pending.results){
  if(p.market==='parlay'&&p.legs){
   const legs:ParlayLeg[]=JSON.parse(p.legs);
   for(const leg of legs){if(leg.result!=='pending')continue;const score=await getScore(leg.gameId,leg.start);if(!score)continue;leg.result=score.void?'void':resultFor(leg.market,leg.side,leg.point,score.away,score.home);leg.score=score.void?'Cancelled':`${score.away}–${score.home}`;}
   const graded=gradeParlay(p.stake_cents,legs);const serialized=JSON.stringify(legs);
   if(serialized===p.legs&&graded.result==='pending')continue;
   const update=await db().prepare("UPDATE picks SET legs=?,result=?,profit_cents=?,settled_at=? WHERE id=? AND result IN ('pending','lost') AND legs=?").bind(serialized,graded.result,graded.profitCents,graded.result==='pending'?null:p.settled_at??new Date().toISOString(),p.id,p.legs).run();
   if(p.result==='pending'&&graded.result!=='pending')count+=Number(update.meta.changes??0);
  }else{
   const score=await getScore(p.game_id,p.start);if(!score)continue;
   const update=await db().prepare("UPDATE picks SET result=?,settled_at=?,score=? WHERE id=? AND result='pending'").bind(score.void?'void':resultFor(p.market,p.side,p.point,score.away,score.home),new Date().toISOString(),score.void?'Cancelled':`${score.away}–${score.home}`,p.id).run();count+=Number(update.meta.changes??0);
  }
 }
 return count;
}
export async function state(mode:string,owner:string){
 const rows=await db().prepare('SELECT * FROM picks WHERE owner=? AND mode=? ORDER BY created_at DESC').bind(owner,mode).all<any>();const history=rows.results;
 const balance=100000+history.reduce((s,p)=>s+(p.result==='pending'?-p.stake_cents:p.result==='won'?p.profit_cents:p.result==='lost'?-p.stake_cents:0),0);
 const settled=history.filter(p=>p.result==='won'||p.result==='lost');const net=settled.reduce((s,p)=>s+(p.result==='won'?p.profit_cents:-p.stake_cents),0),risked=settled.reduce((s,p)=>s+p.stake_cents,0);
 const sentiment=await db().prepare("SELECT game_id,market,side,COUNT(*) AS count FROM picks WHERE mode=? AND market!='parlay' GROUP BY game_id,market,side").bind(mode).all();
 const leaders=await db().prepare("SELECT owner,COUNT(*) AS picks,SUM(CASE WHEN result='won' THEN 1 ELSE 0 END) AS wins,SUM(CASE WHEN result='lost' THEN 1 ELSE 0 END) AS losses,SUM(CASE WHEN result='won' THEN profit_cents WHEN result='lost' THEN -stake_cents ELSE 0 END) AS net FROM picks WHERE mode=? GROUP BY owner ORDER BY net DESC LIMIT 20").bind(mode).all<any>();
 const community=await Promise.all(leaders.results.map(async ({owner:id,...p})=>{const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(id));const tag=Array.from(new Uint8Array(digest)).slice(0,3).map(x=>x.toString(16).padStart(2,'0')).join('').toUpperCase();return {...p,name:id===owner?'You':`Fan ${tag}`};}));
 return {history:history.map(({owner,legs,...p})=>({...p,legs:legs?JSON.parse(legs):null})),balance:balance/100,wins:settled.filter(p=>p.result==='won').length,losses:settled.filter(p=>p.result==='lost').length,pending:history.filter(p=>p.result==='pending').length,roi:risked?net/risked*100:null,sentiment:sentiment.results,community};
}
