'use client';

import { useState, useEffect } from 'react';

import { Terminal, ShieldAlert, Activity, Clock, Lock, Network, Fingerprint } from 'lucide-react';
import Link from 'next/link';

interface Command {
  id: number;
  timestamp: string;
  command: string;
  response: string;
  execution_time_ms: number;
}

interface ThreatEvent {
  id: number;
  timestamp: string;
  event_type: string;
  severity: string;
  data: string;
}

interface SessionDetail {
  session_id: string;
  start_time: string;
  end_time: string | null;
  client_ip: string;
  client_software: string;
  password_used: string;
  status: string;
  threat_score: number;
  commands: Command[];
  threat_events: ThreatEvent[];
}

export default function SessionIntelligenceView({ params }: { params: { id: string } }) {
  const [session, setSession] = useState<SessionDetail | null>(null);

  useEffect(() => {
    const fetchSessionData = async () => {
      try {
        // Fetch session commands
        const cmdRes = await fetch(`http://localhost:8000/api/sessions/${params.id}`);
        const sessionData = await cmdRes.json();
        
        // Fetch all alerts to filter by session_id
        const alertRes = await fetch(`http://localhost:8000/api/alerts`);
        const alertData = await alertRes.json();
        const sessionAlerts = alertData.alerts.filter((a: ThreatEvent & { session_id: string }) => a.session_id === params.id);

        // Fetch the global session list to get the real-time threat score
        const globalRes = await fetch('http://localhost:8000/api/sessions');
        const globalData = await globalRes.json();
        const globalSession = globalData.sessions.find((s: SessionDetail) => s.session_id === params.id);

        setSession({
          ...sessionData,
          threat_events: sessionAlerts,
          threat_score: globalSession?.threat_score || 0
        });

      } catch (e) {
        console.error("Failed to fetch session detail", e);
      }
    };
    
    fetchSessionData();
    const interval = setInterval(fetchSessionData, 2000);
    return () => clearInterval(interval);
  }, [params.id]);

  if (!session) return (
    <div className="min-h-screen bg-zinc-950 p-8 flex items-center justify-center">
      <div className="flex items-center gap-3 text-zinc-500">
        <Activity className="w-5 h-5 animate-spin" />
        Analysing extracellular data...
      </div>
    </div>
  );

  const getSeverityStyle = (severity: string) => {
    if (severity === 'critical') return 'text-red-400 border-red-500/30 bg-red-500/10';
    if (severity === 'high') return 'text-orange-400 border-orange-500/30 bg-orange-500/10';
    if (severity === 'medium') return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
    return 'text-green-400 border-green-500/30 bg-green-500/10';
  };

  const getThreatColor = (score: number) => {
    if (score >= 80) return 'text-red-500';
    if (score >= 60) return 'text-orange-500';
    if (score >= 30) return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <main className="min-h-screen bg-zinc-950 selection:bg-blue-500/30 p-4 sm:p-6 lg:p-8">
      
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center gap-4 mb-2">
          <Link href="/dashboard" className="text-zinc-500 hover:text-white transition-colors bg-zinc-900 border border-zinc-800 p-2 rounded-lg">
            <span className="text-sm font-bold flex items-center gap-1">← Back</span>
          </Link>
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Fingerprint className="w-6 h-6 text-indigo-500" />
              Session Intelligence: {session.session_id.split('-')[0]}
            </h1>
            <div className="flex items-center gap-3 mt-1 text-sm">
              <span className={`flex items-center gap-1.5 ${session.status === 'active' ? 'text-green-400' : 'text-zinc-500'}`}>
                <span className={`relative flex h-2 w-2 ${session.status === 'active' ? '' : 'hidden'}`}>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                {session.status.toUpperCase()}
              </span>
              <span className="text-zinc-600">•</span>
              <span className="text-zinc-400 flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(session.start_time).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col: Profile & Alerts */}
        <div className="space-y-6">
          
          {/* Attacker Profile */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
             <div className="p-4 bg-zinc-950 border-b border-zinc-800 flex justify-between items-center">
               <h3 className="font-bold text-white flex items-center gap-2">
                 <Network className="w-4 h-4 text-blue-500" /> Attacker Profile
               </h3>
               {/* Threat Gauge */}
               <div className="flex items-center gap-2">
                 <span className="text-zinc-500 text-xs font-bold uppercase">Threat Score</span>
                 <span className={`text-xl font-black ${getThreatColor(session.threat_score)}`}>{session.threat_score}</span>
               </div>
             </div>
             <div className="p-5 space-y-4">
               <div>
                  <p className="text-xs text-zinc-500 uppercase font-semibold mb-1">Origin IP</p>
                  <p className="font-mono text-white text-lg bg-zinc-950 p-2 rounded border border-zinc-800">{session.client_ip}</p>
               </div>
               <div className="grid grid-cols-2 gap-4">
                 <div>
                    <p className="text-xs text-zinc-500 uppercase font-semibold mb-1">Credentials</p>
                    <p className="font-mono text-zinc-300 text-sm flex items-center gap-1">
                      <Lock className="w-3 h-3" /> user:{session.password_used || '***'}
                    </p>
                 </div>
                 <div>
                    <p className="text-xs text-zinc-500 uppercase font-semibold mb-1">Duration</p>
                    <p className="text-zinc-300 text-sm">{session.end_time ? 'Closed' : 'Live'}</p>
                 </div>
               </div>
               <div>
                  <p className="text-xs text-zinc-500 uppercase font-semibold mb-1">Client Software Fingerprint</p>
                  <p className="font-mono text-zinc-400 text-xs truncate">{session.client_software}</p>
               </div>
             </div>
          </div>

          {/* Session Alerts */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col h-[400px]">
            <div className="p-4 bg-zinc-950 border-b border-zinc-800 flex justify-between items-center">
               <h3 className="font-bold text-white flex items-center gap-2">
                 <ShieldAlert className="w-4 h-4 text-red-500" /> Session Threats
               </h3>
               <span className="text-xs bg-red-500/10 text-red-400 px-2 py-0.5 rounded font-bold">{session.threat_events.length}</span>
            </div>
            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              {session.threat_events.length === 0 ? (
                <p className="text-zinc-500 text-sm text-center mt-10">No specific threat events logged yet.</p>
              ) : (
                session.threat_events.map((t) => (
                  <div key={t.id} className="p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-sm font-bold text-white capitalize">{t.event_type.replace('_', ' ')}</span>
                      <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${getSeverityStyle(t.severity)}`}>{t.severity}</span>
                    </div>
                    <span className="text-xs text-zinc-500">{new Date(t.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

        {/* Right Col: Timeline */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col h-[800px]">
           <div className="p-4 bg-zinc-950 border-b border-zinc-800 flex justify-between items-center">
             <h3 className="font-bold text-white flex items-center gap-2">
               <Terminal className="w-4 h-4 text-green-500" /> Command Timeline feed
             </h3>
             <span className="text-xs text-zinc-500">{session.commands?.length || 0} Commands Executed</span>
           </div>
           
           <div className="p-4 overflow-y-auto flex-1 bg-zinc-950 space-y-4 font-mono text-sm shadow-inner">
             {(!session.commands || session.commands.length === 0) ? (
               <div className="h-full flex flex-col items-center justify-center text-zinc-600">
                 <Activity className="w-8 h-8 mb-2 opacity-50" />
                 <p>Waiting for attacker input...</p>
               </div>
             ) : (
               session.commands.map((cmd) => (
                 <div key={cmd.id} className="border-l-2 border-zinc-800 pl-4 py-1 relative">
                   <div className="absolute -left-[5px] top-2 w-2 h-2 rounded-full bg-zinc-700"></div>
                   
                   <div className="text-zinc-500 text-[11px] mb-1 flex items-center gap-2">
                     {new Date(cmd.timestamp).toLocaleTimeString()}
                     {cmd.execution_time_ms > 0 && <span className="text-zinc-600">({cmd.execution_time_ms}ms)</span>}
                   </div>
                   
                   <div className="text-green-400 mb-1 flex items-start gap-2">
                     <span className="text-zinc-600 select-none">$</span>
                     <span className="break-all">{cmd.command}</span>
                   </div>
                   
                   {cmd.response && (
                     <div className="text-zinc-400 bg-zinc-900/50 p-2 rounded whitespace-pre-wrap text-[13px] border border-zinc-800/50 mt-2 max-h-60 overflow-y-auto overflow-x-hidden">
                       {cmd.response}
                     </div>
                   )}
                 </div>
               ))
             )}
             
             {/* Blinking cursor for active sessions attached to bottom */}
             {session.status === 'active' && (
               <div className="pl-4 pt-2">
                  <span className="text-zinc-600 mr-2">$</span>
                  <span className="inline-block w-2.5 h-4 bg-zinc-500 animate-pulse align-middle"></span>
               </div>
             )}
           </div>
        </div>

      </div>
    </main>
  );
}
