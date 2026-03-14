'use client';

import { useState, useEffect } from 'react';
import { AlertTriangle, Fingerprint, MapPin, Terminal } from 'lucide-react';

interface ThreatEvent {
  id: number;
  session_id: string;
  timestamp: string;
  threat_type: string;
  severity: string;
  details: string;
  client_ip: string;
}

export function LiveAlerts() {
  const [alerts, setAlerts] = useState<ThreatEvent[]>([]);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/alerts');
        const data = await res.json();
        setAlerts(data.alerts.slice(0, 50)); // Keep only latest 50
      } catch (e) {
        console.error("Failed to fetch alerts", e);
      }
    };
    
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 3000);
    return () => clearInterval(interval);
  }, []);

  const getAlertIcon = (type: string) => {
    if (type === 'api_probe') return <AlertTriangle className="w-5 h-5 text-orange-500" />;
    if (type === 'recon_burst') return <Terminal className="w-5 h-5 text-blue-500" />;
    if (type === 'geo_lookup') return <MapPin className="w-5 h-5 text-purple-500" />;
    return <Fingerprint className="w-5 h-5 text-zinc-500" />;
  };

  const getSeverityStyle = (severity: string) => {
    if (severity === 'critical') return 'text-red-400 border-red-500/30 bg-red-500/10';
    if (severity === 'high') return 'text-orange-400 border-orange-500/30 bg-orange-500/10';
    if (severity === 'medium') return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
    return 'text-green-400 border-green-500/30 bg-green-500/10';
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-2xl flex flex-col h-[600px]">
      <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-500" />
          Live Threat Feed
        </h3>
        <span className="px-2 py-1 bg-red-500/10 text-red-400 text-xs font-bold rounded animate-pulse">LIVE</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {alerts.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-zinc-500">
            <ShieldAlert className="w-12 h-12 mb-4 opacity-20" />
            <p>No active threats detected</p>
          </div>
        ) : (
          alerts.map((alert, i) => (
            <div key={`${alert.session_id}-${i}`} className="bg-zinc-950 border border-zinc-800 rounded-xl p-4 flex gap-4 animate-in fade-in slide-in-from-top-2">
              <div className="flex-shrink-0 mt-1">
                {getAlertIcon(alert.threat_type)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white font-medium capitalize flex items-center gap-2">
                    {alert.threat_type.replace('_', ' ')}
                    {alert.client_ip && <span className="text-zinc-500 text-xs px-2 py-0.5 bg-zinc-800 rounded">{alert.client_ip}</span>}
                  </span>
                  <span className="text-xs text-zinc-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-zinc-400 text-sm truncate">{alert.details}</p>
              </div>
              <div className="flex-shrink-0 flex items-center">
                <span className={`text-xs font-bold px-2 py-1 rounded border uppercase ${getSeverityStyle(alert.severity)}`}>
                  {alert.severity}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Just for the fallback icon
import { ShieldAlert } from 'lucide-react';
