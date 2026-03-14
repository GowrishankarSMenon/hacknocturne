'use client';

import { useState, useEffect, use } from 'react';
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
  threat_type: string;
  severity: string;
  details: string;
  data: string;
  display_type?: string;
  display_time?: string;
}

interface SessionDetail {
  session_id: string;
  start_time: string;
  end_time: string | null;
  client_ip: string;
  client_software: string;
  password_used: string;
  client_port: number;
  status: string;
  threat_score: number;
  classification: string;
  avg_ipd: number;
  commands: Command[];
  threat_events: ThreatEvent[];
}

const getSeverityStyle = (severity: string) => {
  const s = String(severity || '').toLowerCase();
  if (s === 'critical') return 'text-red-400 border-red-500/30 bg-red-500/10';
  if (s === 'high') return 'text-orange-400 border-orange-500/30 bg-orange-500/10';
  if (s === 'medium') return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
  return 'text-green-400 border-green-500/30 bg-green-500/10';
};

const getThreatColor = (score: number) => {
  if (score >= 80) return 'text-red-500';
  if (score >= 60) return 'text-orange-500';
  if (score >= 30) return 'text-yellow-500';
  return 'text-green-500';
};

const getClassificationBadge = (classification: string) => {
  const c = String(classification || '').toLowerCase();
  if (c === 'bot') return <span className="flex items-center gap-1 bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">Automated Bot</span>;
  if (c === 'suspicious') return <span className="flex items-center gap-1 bg-orange-500/10 text-orange-400 border border-orange-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">Suspicious Script</span>;
  if (c === 'human') return <span className="flex items-center gap-1 bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">Human Attacker</span>;
  return <span className="flex items-center gap-1 bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider">Analyzing Pattern...</span>;
};

export default function SessionIntelligenceView({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const sessionId = unwrappedParams.id;
  const [session, setSession] = useState<SessionDetail | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    
    const fetchSessionData = async () => {
      try {
        const detailsRes = await fetch(`http://localhost:8000/api/sessions/${sessionId}`);
        const sessionData = await detailsRes.json();
        
        const alertRes = await fetch(`http://localhost:8000/api/alerts`);
        const alertData = await alertRes.json();
        const rawAlerts = alertData.alerts.filter((a: any) => a.session_id === sessionId);
        
        const processedAlerts = rawAlerts.map((a: any) => ({
          ...a,
          display_type: String(a.threat_type || a.event_type || 'Unknown').split('_').join(' '),
          display_time: a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : 'N/A'
        }));

        const globalRes = await fetch('http://localhost:8000/api/sessions');
        const globalData = await globalRes.json();
        const globalSession = globalData.sessions.find((s: any) => s.session_id === sessionId);

        let finalScore = globalSession?.threat_score || 0;
        if (globalSession?.classification === 'bot') finalScore = Math.max(finalScore, 85);
        if (globalSession?.classification === 'suspicious') finalScore = Math.max(finalScore, 45);

        setSession({
          ...sessionData,
          classification: globalSession?.classification || 'unknown',
          avg_ipd: globalSession?.avg_ipd || 0,
          threat_events: processedAlerts,
          threat_score: finalScore
        });

      } catch (e) {
        console.error("Failed to fetch session detail", e);
      }
    };
    
    fetchSessionData();
    const interval = setInterval(fetchSessionData, 2000);
    return () => clearInterval(interval);
  }, [sessionId]);

  if (!session) return (
    <div className="min-h-screen bg-zinc-950 p-8 flex items-center justify-center">
      <div className="flex items-center gap-3 text-zinc-500">
        <Activity className="w-5 h-5 animate-spin" />
        Analysing extracellular data...
      </div>
    </div>
  );

  return (
    <main className="min-h-screen bg-zinc-950 selection:bg-blue-500/30 p-4 sm:p-6 lg:p-8 notranslate" translate="no">
      
      <div className="max-w-7xl mx-auto mb-8">
        <div className="flex items-center gap-4 mb-2">
          <Link href="/dashboard" className="text-zinc-500 hover:text-white transition-colors bg-zinc-900 border border-zinc-800 p-2 rounded-lg">
            <span className="text-sm font-bold flex items-center gap-1">← Back</span>
          </Link>
          <div className="flex-1">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2">
                    <Fingerprint className="w-6 h-6 text-indigo-500" />
                    Session Intelligence: {String(session.session_id).split('-')[0]}
                </h1>
                {getClassificationBadge(session.classification)}
            </div>
            <div className="flex items-center gap-3 mt-1 text-sm">
              <span className={`flex items-center gap-1.5 ${session.status === 'active' ? 'text-green-400' : 'text-zinc-500'}`}>
                <span className={`relative flex h-2 w-2 ${session.status === 'active' ? '' : 'hidden'}`}>
                  <span className="absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
                {String(session.status).toUpperCase()}
              </span>
              <span className="text-zinc-600">•</span>
              <span className="text-zinc-400 flex items-center gap-1"><Clock className="w-3 h-3" /> {new Date(session.start_time).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <div className="space-y-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
             <div className="p-4 bg-zinc-950 border-b border-zinc-800 flex justify-between items-center">
               <h3 className="font-bold text-white flex items-center gap-2">
                 <Network className="w-4 h-4 text-blue-500" /> Attacker Profile
               </h3>
               <div className="flex items-center gap-2">
                 <span className="text-zinc-500 text-xs font-bold uppercase">Threat Score</span>
                 <span className={`text-xl font-black ${getThreatColor(session.threat_score)}`}>{session.threat_score}</span>
               </div>
             </div>
             <div className="p-5 space-y-4">
               <div>
                  <p className="text-xs text-zinc-500 uppercase font-semibold mb-1">Origin IP & Port</p>
                  <p className="font-mono text-white text-lg bg-zinc-950 p-2 rounded border border-zinc-800">
                    {String(session.client_ip)}<span className="text-zinc-500 text-sm ml-1">:{session.client_port || '????'}</span>
                  </p>
               </div>
               <div className="grid grid-cols-2 gap-4">
                 <div>
                    <p className="text-xs text-zinc-500 uppercase font-semibold mb-1">Keystroke Analytics</p>
                    <p className="font-mono text-zinc-300 text-sm flex items-center gap-1">
                      <Activity className="w-3 h-3" /> {session.avg_ipd ? `${session.avg_ipd.toFixed(1)}ms` : 'Calculating...'}
                    </p>
                 </div>
                 <div>
                    <p className="text-xs text-zinc-500 uppercase font-semibold mb-1">Credentials</p>
                    <p className="font-mono text-zinc-300 text-sm flex items-center gap-1">
                      <Lock className="w-3 h-3" /> {String(session.password_used || '***')}
                    </p>
                 </div>
               </div>
               <div>
                  <p className="text-xs text-zinc-500 uppercase font-semibold mb-1">Fingerprint</p>
                  <p className="font-mono text-zinc-400 text-xs truncate bg-zinc-950 p-2 rounded border border-zinc-800/50">{String(session.client_software)}</p>
               </div>
             </div>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col h-[400px]">
            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              {session.threat_events.length === 0 ? (
                <p className="text-zinc-500 text-sm text-center mt-10">No specific threat events logged yet.</p>
              ) : (
                session.threat_events.map((t) => (
                  <div key={t.id} className="p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-sm font-bold text-white capitalize">
                        {t.display_type}
                      </span>
                      <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${getSeverityStyle(t.severity)}`}>{t.severity}</span>
                    </div>
                    <span className="text-xs text-zinc-500">
                      {t.display_time}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

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
                     <span className="break-all">{String(cmd.command)}</span>
                   </div>
                   
                   {cmd.response && (
                     <pre className="text-zinc-400 bg-zinc-900/50 p-2 rounded whitespace-pre-wrap text-[13px] border border-zinc-800/50 mt-2 max-h-60 overflow-y-auto overflow-x-hidden notranslate" translate="no">
                       {String(cmd.response)}
                     </pre>
                   )}
                 </div>
               ))
             )}
             
             {session.status === 'active' && (
               <div className="pl-4 pt-2">
                  <span className="text-zinc-600 mr-2">$</span>
                  <span className="inline-block w-2.5 h-4 bg-zinc-500 align-middle"></span>
               </div>
             )}
           </div>
        </div>

      </div>
    </main>
  );
}
