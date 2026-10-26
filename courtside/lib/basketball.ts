export type Market='moneyline'|'spread'|'total';
export type Game={id:string;away:string;home:string;awayCode:string;homeCode:string;awayColor:string;homeColor:string;time:string;spread:number;total:number;awayOdds:number;homeOdds:number;start?:string;source?:string;fetchedAt?:string;prices?:number[]};
export const games:Game[]=[
 {id:'demo-bos-nyk',away:'Boston Celtics',home:'New York Knicks',awayCode:'BOS',homeCode:'NYK',awayColor:'#58ba8c',homeColor:'#ef9f60',time:'7:30 PM',spread:4.5,total:224.5,awayOdds:-185,homeOdds:155},
 {id:'demo-lal-gsw',away:'Los Angeles Lakers',home:'Golden State Warriors',awayCode:'LAL',homeCode:'GSW',awayColor:'#c69de7',homeColor:'#f0cc6a',time:'10:00 PM',spread:-3.5,total:232.5,awayOdds:135,homeOdds:-160},
 {id:'demo-den-okc',away:'Denver Nuggets',home:'Oklahoma City Thunder',awayCode:'DEN',homeCode:'OKC',awayColor:'#eac97c',homeColor:'#7bc5ec',time:'8:00 PM',spread:-6.5,total:228.5,awayOdds:210,homeOdds:-250},
 {id:'demo-mil-cle',away:'Milwaukee Bucks',home:'Cleveland Cavaliers',awayCode:'MIL',homeCode:'CLE',awayColor:'#85b8a0',homeColor:'#d28799',time:'7:00 PM',spread:-5.5,total:221.5,awayOdds:180,homeOdds:-215}
];
const logoSlugs:Record<string,string>={GSW:'gs',NYK:'ny',NOP:'no',SAS:'sa',PHO:'phx',WAS:'wsh',BRK:'bkn',CHO:'cha',UTA:'utah'};
export const teamLogo=(code:string)=>`https://a.espncdn.com/i/teamlogos/nba/500/${logoSlugs[code.toUpperCase()]??code.toLowerCase()}.png`;
export const signed=(n:number)=>n>0?'+'+n:String(n);
export function quote(g:Game,market:Market,side:number){
 const team=side===0?g.awayCode:g.homeCode;
 const point=market==='spread'?(side===0?-g.spread:g.spread):market==='total'?g.total:null;
 return {label:market==='moneyline'?team:market==='spread'?`${team} ${signed(point!)}`:`${side===0?'Over':'Under'} ${point}`,odds:market==='moneyline'?(side===0?g.awayOdds:g.homeOdds):(g.prices?.[(market==='spread'?0:2)+side]??-110),point};
}
export function profit(stake:number,odds:number){return Math.round(stake*(odds>0?odds/100:100/-odds)*100)/100}
