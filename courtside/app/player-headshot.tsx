'use client';
import {useState} from 'react';
import headshots from '@/lib/player-headshots.json';

// BALLDONTLIE IDs and NBA IDs are different. Match the saved name as well so
// replacing the prediction CSV cannot silently attach another player's photo.
const normalize = (name:string) => name.normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]/g,'');
export default function PlayerHeadshot({playerId,name}:{playerId:number;name:string}) {
 const entry=(headshots as Record<string,{name:string;nbaId:number}>)[String(playerId)];
 const url=entry&&normalize(entry.name)===normalize(name)?`https://cdn.nba.com/headshots/nba/latest/260x190/${entry.nbaId}.png`:null;
 const [failedUrl,setFailedUrl]=useState<string|null>(null);
 const initials=name.trim().split(/\s+/).filter(Boolean).slice(0,2).map(part=>part[0]).join('').toUpperCase();
 return url&&failedUrl!==url
  ? <img className="player-headshot" src={url} alt="" width={44} height={44} loading="lazy" decoding="async" onError={()=>setFailedUrl(url)}/>
  : <span className="player-headshot player-headshot-fallback" aria-hidden="true">{initials}</span>;
}
