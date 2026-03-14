'use client';

import { useState, useEffect } from 'react';
import { Terminal, Lock, Fingerprint, AlertTriangle } from 'lucide-react';

interface Session {
  session_id: string;
  start_time: string;
  client_ip: string;
  client_software: string;
  password_used: string;
  status: string;
  threat_score: number;
}

interface Correlation {
  hassh: string;
  ips: string[];
  ip_count: number;
  sessions: string[];
  usernames: string[];
}

export function SessionTracker() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [correlations, setCorrelations] = useState<Correlation[]>([]);
  const [hasshMap, setHashhMap] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sessRes, hasshRes] = await Promise.all([
          fetch('http://localhost:8000/api/sessions'),
          fetch('http://localhost:8000/api/hassh'),
        ]);
        const sessData = await sessRes.json();
        setSessions(sessData.sessions?.slice(0, 10) || []);
        if (hasshRes.ok) {
          const hasshData = await hasshRes.json();
          const map: Record<string, string> = {};
          for (const fp of hasshData.fingerprints || []) {
            if (fp.session_id && fp.hassh) map[fp.session_id] = fp.hassh;
          }
          setHashhMap(map);
          setCorrelations(hasshData.correlations || []);
        }
      } catch (e) { console.error("Failed to fetch sessions", e); }
    };
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-rose-400 bg-rose-500/10';
    if (score >= 60) return 'text-orange-400 bg-orange-500/10';
    if (score >= 30) return 'text-amber-400 bg-amber-500/10';
    return 'text-emerald-400 bg-emerald-500/10';
  };

  return (
    <div className="space-y-4">
      <div className="glass rounded-2xl flex flex-col h-[540px]">
        <div className="p-5 border-b border-zinc-800/50 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Terminal className="w-4 h-4 text-indigo-500" />
            Active Sessions
          </h3>
          <span className="text-xs text-zinc-500">{sessions.length} recorded</span>
        </div>
        
        <div className="flex-1 overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-zinc-800/30">
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Status</th>
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Origin</th>
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Password</th>
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Score</th>
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">HASSH</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map(session => {
                const hassh = hasshMap[session.session_id] || null;
                return (
                  <tr 
                    key={session.session_id}
                    onClick={() => window.location.href = `/dashboard/${session.session_id}`}
                    className="border-b border-zinc-800/20 hover:bg-white/[0.02] transition-colors cursor-pointer"
                  >
                    <td className="px-5 py-3">
                      {session.status === 'active' ? (
                        <span className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
                          <span className="relative flex h-1.5 w-1.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                          </span>
                          Active
                        </span>
                      ) : (
                        <span className="text-zinc-600 text-xs">Closed</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <span className="text-white font-mono text-xs">{String(session.client_ip || '—')}</span>
                    </td>
                    <td className="px-5 py-3">
                      <span className="text-zinc-400 font-mono text-xs flex items-center gap-1">
                        <Lock className="w-3 h-3 text-zinc-600" />
                        {String(session.password_used || '***')}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${getScoreColor(session.threat_score || 0)}`}>
                        {session.threat_score || 0}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {hassh ? (
                        <span className="font-mono text-[10px] text-zinc-500 flex items-center gap-1">
                          <Fingerprint className="w-3 h-3 text-indigo-400" />
                          {hassh.substring(0, 12)}...
                        </span>
                      ) : (
                        <span className="text-zinc-700 text-[10px]">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cross-IP Correlation */}
      {correlations.length > 0 && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="p-4 border-b border-zinc-800/50 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-rose-500" />
            <h3 className="text-sm font-semibold text-white">Cross-IP Correlation</h3>
            <span className="text-[10px] text-zinc-500 ml-auto">{correlations.length} match{correlations.length !== 1 ? 'es' : ''}</span>
          </div>
          <div className="p-3 space-y-2">
            {correlations.map((c, i) => (
              <div key={i} className="bg-rose-500/5 border-l-2 border-rose-500 rounded-r-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <Fingerprint className="w-3.5 h-3.5 text-rose-400" />
                  <code className="text-[10px] text-indigo-400">{c.hassh.substring(0, 20)}...</code>
                </div>
                <p className="text-[11px] text-zinc-500">
                  Seen from <span className="text-rose-400 font-semibold">{c.ip_count}</span> IPs: {c.ips.join(', ')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
