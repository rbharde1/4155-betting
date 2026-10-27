import Dashboard from '../dashboard';
import {requireChatGPTUser} from '../chatgpt-auth';
export const dynamic='force-dynamic';
export default async function DashboardPage(){await requireChatGPTUser('/dashboard');return <Dashboard/>}
