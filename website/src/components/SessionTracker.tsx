'use client';

import { useState, useEffect } from 'react';
import { Terminal, Shield, Eye, Lock } from 'lucide-react';

interface Session {
  session_id: string;
  start_time: string;
  end_time: string | null;
  client_ip: string;
  client_software: string;
  password_used: string;
  status: string;
  threat_score: number;
}

export function SessionTracker() {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/sessions');
        const data = await res.json();
        setSessions(data.sessions.slice(0, 10)); // Current 10 sessions
      } catch (e) {
        console.error("Failed to fetch sessions", e);
      }
    };
    
    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-red-400 bg-red-500/10 border-red-500/30';
    if (score >= 60) return 'text-orange-400 bg-orange-500/10 border-orange-500/30';
    if (score >= 30) return 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30';
    return 'text-green-400 bg-green-500/10 border-green-500/30';
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl flex flex-col h-[600px]">
      <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <Terminal className="w-5 h-5 text-indigo-500" />
          Active Extracellular Sessions
        </h3>
        <span className="text-sm font-medium text-zinc-400">{sessions.length} recorded</span>
      </div>
      
      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-950/50">
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Origin IP</th>
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Credentials</th>
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Threat Score</th>
              <th className="px-6 py-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">Duration</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50 cursor-pointer">
            {sessions.map((session) => (
              <tr 
                key={session.session_id} 
                onClick={() => window.location.href = `/dashboard/${session.session_id}`}
                className="hover:bg-zinc-800/40 transition-colors"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  {session.status === 'active' ? (
                    <span className="flex items-center gap-2 text-green-400 text-sm font-medium">
                      <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                      </span>
                      Active
                    </span>
                  ) : (
                    <span className="flex items-center gap-2 text-zinc-500 text-sm font-medium">
                      <span className="relative flex h-2 w-2">
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-zinc-600"></span>
                      </span>
                      Closed
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-white font-mono text-sm">{String(session.client_ip || 'unknown')}</span>
                  <p className="text-xs text-zinc-500 truncate max-w-[150px]">{String(session.client_software || 'Generic SSH Client')}</p>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="flex items-center gap-1.5 text-zinc-300 text-sm font-mono bg-zinc-950 px-2 py-1 rounded inline-flex border border-zinc-800">
                    <Lock className="w-3 h-3 text-zinc-500" />
                    {String(session.password_used || '***')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 rounded border text-xs font-bold ${getScoreColor(session.threat_score || 0)}`}>
                    {session.threat_score || 0} / 100
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-zinc-400">
                  {session.start_time ? new Date(session.start_time).toLocaleTimeString() : 'N/A'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
