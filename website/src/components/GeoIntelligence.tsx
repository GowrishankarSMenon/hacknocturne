'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { Globe, MapPin } from 'lucide-react';

const Map = dynamic(() => import('./MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="h-[400px] w-full rounded-xl bg-zinc-900/50 animate-pulse flex items-center justify-center text-zinc-600">
      <Globe className="w-6 h-6 opacity-30" />
    </div>
  ),
});

interface SessionGeo {
  session_id: string;
  client_ip: string;
  username: string;
  geo?: { city: string; country: string; isp: string; lat: number; lon: number };
}

export function GeoIntelligence() {
  const [sessions, setSessions] = useState<SessionGeo[]>([]);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/sessions');
        const data = await res.json();
        setSessions((data.sessions || []).filter((s: SessionGeo) => s.geo));
      } catch (e) { console.error('Failed to fetch sessions', e); }
    };
    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-4">
      {/* Global Map */}
      <div className="glass rounded-2xl overflow-hidden">
        <div className="p-5 border-b border-zinc-800/50 flex items-center gap-2">
          <Globe className="w-4 h-4 text-violet-500" />
          <h3 className="text-sm font-semibold text-white">Global Threat Map</h3>
          <span className="text-xs text-zinc-500 ml-auto">{sessions.length} origin{sessions.length !== 1 ? 's' : ''}</span>
        </div>
        <div className="p-1">
          <Map geoData={sessions} />
        </div>
      </div>

      {/* Attacker Origins Table */}
      {sessions.length > 0 && (
        <div className="glass rounded-2xl overflow-hidden">
          <div className="p-5 border-b border-zinc-800/50">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <MapPin className="w-4 h-4 text-violet-500" /> Attacker Origins
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-zinc-800/30">
                  <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">IP</th>
                  <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">Location</th>
                  <th className="px-5 py-3 text-[10px] font-semibold text-zinc-500 uppercase tracking-wider">ISP</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => (
                  <tr key={s.session_id} className="border-b border-zinc-800/20 hover:bg-white/[0.02] transition-colors">
                    <td className="px-5 py-3 font-mono text-xs text-blue-400">{s.client_ip}</td>
                    <td className="px-5 py-3 text-xs text-zinc-300">{s.geo?.city}, {s.geo?.country}</td>
                    <td className="px-5 py-3 text-xs text-zinc-500">{s.geo?.isp || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
