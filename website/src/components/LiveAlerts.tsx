'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { AlertTriangle, Fingerprint, MapPin, Terminal, ShieldAlert, ArrowRight } from 'lucide-react';

interface ThreatEvent {
  id: number;
  session_id: string;
  timestamp: string;
  threat_type: string;
  severity: string;
  details: string;
  client_ip: string;
  display_type?: string;
}

const getSeverityStyle = (severity: string) => {
  const s = String(severity || '').toLowerCase();
  if (s === 'critical') return 'text-rose-400 bg-rose-500/10';
  if (s === 'high') return 'text-orange-400 bg-orange-500/10';
  if (s === 'medium') return 'text-amber-400 bg-amber-500/10';
  return 'text-emerald-400 bg-emerald-500/10';
};

export function LiveAlerts() {
  const [alerts, setAlerts] = useState<ThreatEvent[]>([]);
  const router = useRouter();

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/alerts');
        const data = await res.json();
        const rawAlerts = data.alerts?.slice(0, 50) || [];
        const processed = rawAlerts.map((alert: any) => ({
          ...alert,
          display_type: String(alert.threat_type || 'Unknown').split('_').join(' '),
        }));
        setAlerts(processed);
      } catch (e) { console.error("Failed to fetch alerts", e); }
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="glass rounded-2xl flex flex-col h-[540px]">
      <div className="p-5 border-b border-zinc-800/50 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-500" />
          Live Threat Feed
        </h3>
        <span className="px-2 py-0.5 bg-rose-500/10 text-rose-400 text-[10px] font-bold rounded-full uppercase tracking-wider">Live</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {alerts.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-zinc-600">
            <ShieldAlert className="w-8 h-8 mb-2 opacity-30" />
            <p className="text-xs">No active threats</p>
          </div>
        ) : (
          alerts.map((alert, i) => (
            <div 
              key={`${alert.session_id}-${alert.id || i}`} 
              className="bg-zinc-900/40 rounded-xl p-3 flex gap-3 cursor-pointer hover:bg-zinc-800/40 transition-all group border border-transparent hover:border-zinc-700/50"
              onClick={() => alert.session_id && router.push(`/dashboard/${alert.session_id}`)}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-white capitalize truncate">{alert.display_type}</span>
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full uppercase ${getSeverityStyle(alert.severity)}`}>
                    {alert.severity || 'low'}
                  </span>
                </div>
                <p className="text-[11px] text-zinc-500 truncate">{alert.details || 'No details'}</p>
                <div className="flex items-center gap-2 mt-1">
                  {alert.client_ip && <span className="text-[10px] text-zinc-600 font-mono">{alert.client_ip}</span>}
                  <span className="text-[10px] text-zinc-700">
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString() : ''}
                  </span>
                </div>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-zinc-700 group-hover:text-zinc-400 transition-colors mt-1 flex-shrink-0" />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
