import {liveBoard} from '@/lib/espn';
export const dynamic='force-dynamic';
export async function GET(request:Request){try{return Response.json({...await liveBoard(),mode:'live'},{headers:{'Cache-Control':'no-store'}});}catch(e){return Response.json({error:(e as Error).message,games:[],mode:'live'},{status:503});}}
