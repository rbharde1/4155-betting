'use client';
import {useState} from 'react';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {ShieldCheck} from 'lucide-react';
export default function Login(){
 const [signup,setSignup]=useState(false);
 return <div className="auth-page"><form className="auth-card" onSubmit={e=>{e.preventDefault();window.location.href='/dashboard'}}>
  <div className="brand"><span className="brand-icon">C</span>COURTSIDE<span className="brand-dot">®</span></div>
  <h1>{signup?'Create your account':'Welcome back'}</h1>
  <p className="auth-sub">{signup?'Start with 1,000 paper points. No real money.':'Sign in to your clubhouse and paper picks.'}</p>
  {signup&&<><label htmlFor="name">DISPLAY NAME</label><Input id="name" autoComplete="nickname"/></>}
  <label htmlFor="email">EMAIL</label><Input id="email" type="email" autoComplete="email"/>
  <label htmlFor="password">PASSWORD</label><Input id="password" type="password" autoComplete={signup?'new-password':'current-password'}/>
  <Button type="submit" className="lock-button">{signup?'Create account':'Sign in'}</Button>
  <button type="button" className="auth-switch" onClick={()=>setSignup(!signup)}>{signup?'Already have an account? Sign in':'New here? Create an account'}</button>
  <div className="slip-foot"><ShieldCheck size={14}/>100% paper. 0% financial risk.</div>
 </form></div>;
}
