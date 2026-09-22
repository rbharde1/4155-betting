import {liveBoard} from '@/lib/espn';
import {games} from '@/lib/basketball';
export const dynamic='force-dynamic';
export async function GET(request:Request){if(new URL(request.url).searchParams.get('mode')==='demo')return Response.json({games,fetchedAt:null,mode:'demo'});try{return Response.json({...await liveBoard(),mode:'live'},{headers:{'Cache-Control':'no-store'}});}catch(e){return Response.json({error:(e as Error).message,games:[],mode:'live'},{status:503});}}
