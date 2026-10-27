export const WEEKLY_POINTS=100;
export const QUALIFYING_PICKS=1;
// Resolve Eastern midnight independently at both boundaries to handle DST weeks.
function easternMidnight(date:Date){
 const target=date.getTime();let utc=target;
 for(let i=0;i<3;i++){
  const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date(utc));
  const p=Object.fromEntries(parts.map(x=>[x.type,x.value]));
  const local=Date.UTC(+p.year,+p.month-1,+p.day,+p.hour,+p.minute,+p.second);
  utc+=target-local;
 }
 return new Date(utc).toISOString();
}
export function competitionWeek(now=new Date()){
 const parts=new Intl.DateTimeFormat('en-US',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
 const p=Object.fromEntries(parts.map(x=>[x.type,x.value]));
 const monday=new Date(Date.UTC(+p.year,+p.month-1,+p.day));
 monday.setUTCDate(monday.getUTCDate()-(monday.getUTCDay()+6)%7);
 const next=new Date(monday);next.setUTCDate(next.getUTCDate()+7);
 return {start:easternMidnight(monday),end:easternMidnight(next)};
}
export function weeklySummary(history:any[],week=competitionWeek()){
 const rows=history.filter(p=>p.created_at>=week.start&&p.created_at<week.end);
 const settled=rows.filter(p=>p.result==='won'||p.result==='lost');
 const net=settled.reduce((sum,p)=>sum+(p.result==='won'?p.profit_cents:-p.stake_cents),0);
 const reserved=rows.filter(p=>p.result==='pending').reduce((sum,p)=>sum+p.stake_cents,0);
 return {...week,balance:(WEEKLY_POINTS*100+net-reserved)/100,net:net/100,settled:settled.length,qualified:settled.length>=QUALIFYING_PICKS};
}
