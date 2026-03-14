'use client';

import { useState, useEffect, useMemo } from 'react';
import { BarChart3, Clock, Activity, Users } from 'lucide-react';

interface Session {
  session_id: string;
  start_time: string;
  end_time: string | null;
  client_ip: string;
  client_port: number;
  username: string;
  password_used: string;
  client_software: string;
  avg_ipd: number;
  threat_score: number;
  status: string;
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

export function Analytics() {
  const [sessions, setSessions] = useState<Session[]>([]);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/sessions');
        const data = await res.json();
        setSessions(data.sessions || []);
      } catch (e) { console.error("Failed to fetch sessions for analytics", e); }
    };
    fetchSessions();
  }, []);

  const heatmapData = useMemo(() => {
    const counts: Record<string, Record<number, number>> = {};
    DAYS.forEach(d => { counts[d] = {}; HOURS.forEach(h => counts[d][h] = 0); });
    let maxCount = 0;
    sessions.forEach(s => {
      if (!s.start_time) return;
      const d = new Date(s.start_time);
      const dayIdx = d.getDay() === 0 ? 6 : d.getDay() - 1;
      const dayName = DAYS[dayIdx];
      const hour = d.getHours();
      counts[dayName][hour]++;
      maxCount = Math.max(maxCount, counts[dayName][hour]);
    });
    return { counts, maxCount };
  }, [sessions]);

  const stats = useMemo(() => {
    const uniqueIps = new Set(sessions.map(s => s.client_ip));
    const active = sessions.filter(s => s.status === 'active').length;
    const closed = sessions.filter(s => s.status === 'closed' && s.end_time);
    let avgDurationStr = '0m 0s';
    if (closed.length > 0) {
      const totalMs = closed.reduce((acc, s) => acc + (new Date(s.end_time!).getTime() - new Date(s.start_time).getTime()), 0);
      const avgMs = totalMs / closed.length;
      avgDurationStr = `${Math.floor(avgMs / 60000)}m ${Math.floor((avgMs % 60000) / 1000)}s`;
    }
    return { total: sessions.length, uniqueIps: uniqueIps.size, active, avgDurationStr };
  }, [sessions]);

  return (
    <div className="space-y-4">
      
      {/* Stats Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Sessions', value: stats.total, icon: Activity, color: 'text-blue-400', bg: 'bg-blue-500/10' },
          { label: 'Unique IPs', value: stats.uniqueIps, icon: Users, color: 'text-violet-400', bg: 'bg-violet-500/10' },
          { label: 'Avg Duration', value: stats.avgDurationStr, icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/10' },
          { label: 'Active Now', value: stats.active, icon: BarChart3, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
        ].map((card, i) => (
          <div key={i} className="glass rounded-2xl p-5 flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl ${card.bg} flex items-center justify-center`}>
              <card.icon className={`w-5 h-5 ${card.color}`} />
            </div>
            <div>
              <p className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider">{card.label}</p>
              <p className="text-xl font-bold text-white">{card.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Heatmap */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-5">
          <BarChart3 className="w-4 h-4 text-indigo-500" />
          Session Activity Heatmap
        </h3>
        <div className="overflow-x-auto">
          <div className="min-w-[700px]">
            <div className="flex ml-12 mb-1.5">
              {HOURS.map(h => (
                <div key={h} className="flex-1 text-center text-[9px] text-zinc-600 font-mono">{h.toString().padStart(2, '0')}</div>
              ))}
            </div>
            <div className="space-y-1">
              {DAYS.map(day => (
                <div key={day} className="flex items-center">
                  <div className="w-12 text-[10px] text-zinc-500 text-right pr-3 font-medium">{day}</div>
                  <div className="flex flex-1 gap-0.5">
                    {HOURS.map(hour => {
                      const count = heatmapData.counts[day][hour];
                      const intensity = count === 0 ? 0 : Math.max(0.25, count / (heatmapData.maxCount || 1));
                      return (
                        <div 
                          key={`${day}-${hour}`}
                          className="flex-1 aspect-square rounded group relative cursor-default"
                          style={{
                            backgroundColor: count === 0 ? 'rgba(39, 39, 42, 0.3)' : `rgba(99, 102, 241, ${intensity})`,
                          }}
                        >
                          <span className="opacity-0 group-hover:opacity-100 absolute -top-7 left-1/2 -translate-x-1/2 bg-zinc-800 text-white text-[9px] py-1 px-2 rounded whitespace-nowrap z-10 pointer-events-none transition-opacity border border-zinc-700">
                            {count} at {hour}:00
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Session Ledger */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-zinc-800/50 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Users className="w-4 h-4 text-zinc-500" /> Session Ledger
          </h3>
          <span className="text-xs text-zinc-500">{sessions.length} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-zinc-800/30">
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Time</th>
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Connection</th>
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Password</th>
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">IPD</th>
                <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Client</th>
              </tr>
            </thead>
            <tbody>
              {sessions.sort((a, b) => new Date(b.start_time).getTime() - new Date(a.start_time).getTime()).map(session => (
                <tr key={session.session_id} className="border-b border-zinc-800/20 hover:bg-white/[0.02] transition-colors">
                  <td className="px-5 py-3 text-xs text-zinc-400">{session.start_time ? new Date(session.start_time).toLocaleString() : '—'}</td>
                  <td className="px-5 py-3">
                    <span className="font-mono text-xs text-zinc-300">
                      {session.username}@{session.client_ip}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-orange-400">{session.password_used || '***'}</td>
                  <td className="px-5 py-3 font-mono text-xs text-indigo-400">
                    {session.avg_ipd ? `${session.avg_ipd.toFixed(1)}ms` : '—'}
                  </td>
                  <td className="px-5 py-3 text-[10px] text-zinc-600 font-mono truncate max-w-[150px]" title={session.client_software}>
                    {session.client_software || 'Generic'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
