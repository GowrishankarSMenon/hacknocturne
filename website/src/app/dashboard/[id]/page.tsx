'use client';

import { useState, useEffect, useMemo, use } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import {
  ArrowLeft, Shield, Terminal, Network, Lock, MapPin,
  Activity, Crosshair, Globe, ChevronRight, FileWarning
} from 'lucide-react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const Map = dynamic(() => import('@/components/MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="h-[200px] w-full rounded-xl bg-zinc-900/50 animate-pulse flex items-center justify-center text-zinc-600">
      <Globe className="w-5 h-5 opacity-30" />
    </div>
  ),
});

const DANGEROUS_KEYWORDS = [
  'sudo', 'su ', 'passwd', 'shadow', 'wget', 'curl', 'nc ', 'ncat',
  'nmap', 'chmod', 'rm -rf', 'rm -r', 'mkfifo', 'bash -i', '/etc/passwd',
  '/etc/shadow', '.ssh', 'id_rsa', 'authorized_keys', 'iptables',
  'crontab', 'base64', 'python -c', 'perl -e', 'netcat', 'reverse', 'bind',
];

const getThreatColor = (score: number) => {
  if (score >= 80) return '#f43f5e';
  if (score >= 60) return '#f97316';
  if (score >= 30) return '#eab308';
  return '#22c55e';
};

const getThreatLabel = (score: number) => {
  if (score >= 80) return 'CRITICAL';
  if (score >= 60) return 'HIGH';
  if (score >= 30) return 'MEDIUM';
  return 'LOW';
};

interface SessionData {
  session_id: string;
  client_ip: string;
  username: string;
  status: string;
  start_time: string;
  end_time: string | null;
  client_software: string;
  password_used: string;
  client_port: number;
  classification: string;
  avg_ipd: number;
  threat_score: number;
  geo?: { city: string; country: string; isp: string; lat: number; lon: number };
}

export default function SessionDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [session, setSession] = useState<SessionData | null>(null);
  const [commands, setCommands] = useState<any[]>([]);
  const [intents, setIntents] = useState<any[]>([]);
  const [canaries, setCanaries] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [sessRes, cmdRes, intRes, canRes, alertRes] = await Promise.all([
          fetch(`http://localhost:8000/api/sessions/${id}`),
          fetch(`http://localhost:8000/api/sessions/${id}/commands`),
          fetch(`http://localhost:8000/api/sessions/${id}/intents`),
          fetch(`http://localhost:8000/api/sessions/${id}/canaries`),
          fetch('http://localhost:8000/api/alerts'),
        ]);
        const sessData = await sessRes.json();
        // API returns session object directly (not wrapped in { session: ... })
        setSession(sessData?.session_id ? sessData : (sessData?.session || null));

        setCommands((await cmdRes.json()).commands || []);
        setIntents((await intRes.json()).intents || []);
        setCanaries((await canRes.json()).canaries || []);
        const alertData = await alertRes.json();
        setAlerts((alertData.alerts || []).filter((a: any) => a.session_id === id));
      } catch (e) { console.error('Failed to fetch session', e); }
    };
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [id]);

  const threatScore = useMemo(() => {
    if (!commands.length) return session?.threat_score || 0;
    let score = Math.min(commands.length * 2, 20);
    let dangerous = 0;
    for (const cmd of commands) {
      if (DANGEROUS_KEYWORDS.some(kw => (cmd.command || '').toLowerCase().includes(kw))) dangerous++;
    }
    score += Math.min(dangerous * 10, 60);
    if (commands.length >= 10) score += 10;
    if (commands.length >= 20) score += 10;
    return Math.min(score, 100);
  }, [commands, session]);

  if (!session) {
    return (
      <main className="min-h-screen bg-[#09090b] p-6 lg:p-8 flex items-center justify-center">
        <div className="glass rounded-2xl p-12 text-center">
          <Terminal className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
          <p className="text-zinc-400 text-sm">Loading session data...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#09090b] p-4 sm:p-6 lg:p-8">
      <div className="max-w-[1400px] mx-auto space-y-4">

        {/* Header */}
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="glass p-2 rounded-xl text-zinc-500 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex-1">
            <h1 className="text-lg font-bold text-white tracking-tight">Session Intelligence</h1>
            <p className="text-xs text-zinc-500 font-mono">{id}</p>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${session.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-zinc-800 text-zinc-500'}`}>
            {session.status === 'active' ? '● Live' : '○ Closed'}
          </span>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

          {/* Left — Profile + Map */}
          <div className="lg:col-span-3 space-y-4">
            <div className="glass rounded-2xl overflow-hidden">
              <div className="p-4 border-b border-zinc-800/30 flex justify-between items-center">
                <h3 className="text-xs font-semibold text-white flex items-center gap-1.5"><Network className="w-3.5 h-3.5 text-blue-500" /> Profile</h3>
                <span className="text-lg font-black" style={{ color: getThreatColor(threatScore) }}>{threatScore}</span>
              </div>
              <div className="p-4 space-y-2.5 text-[11px]">
                {[
                  { label: 'IP Address', value: session.client_ip, style: 'text-blue-400 font-mono' },
                  { label: 'Location', value: session.geo ? `${session.geo.city}, ${session.geo.country}` : 'Unknown' },
                  { label: 'ISP', value: session.geo?.isp || 'Unknown', style: 'text-zinc-400' },
                  { label: 'SSH Client', value: session.client_software || '—', style: 'font-mono text-zinc-400 truncate' },
                  { label: 'Password', value: session.password_used || '***', style: 'text-orange-400 font-mono' },
                  { label: 'Keystroke IPD', value: session.avg_ipd ? `${session.avg_ipd.toFixed(1)}ms` : '—', style: 'text-indigo-400 font-mono' },
                ].map((f, i) => (
                  <div key={i}>
                    <p className="text-[9px] text-zinc-600 uppercase font-semibold">{f.label}</p>
                    <p className={`${f.style || 'text-zinc-300'}`}>{f.value}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Threat Gauge */}
            <div className="glass rounded-2xl p-5">
              <div className="relative h-24 flex items-center justify-center">
                <Doughnut
                  data={{
                    labels: ['Threat', 'Safe'],
                    datasets: [{ data: [threatScore, 100 - threatScore], backgroundColor: [getThreatColor(threatScore), '#18181b'], borderWidth: 0, borderRadius: 2, circumference: 180, rotation: 270 }],
                  }}
                  options={{ cutout: '80%', plugins: { tooltip: { enabled: false }, legend: { display: false } }, maintainAspectRatio: false }}
                />
                <div className="absolute inset-0 flex flex-col items-center justify-center mt-4">
                  <span className="text-xl font-black" style={{ color: getThreatColor(threatScore) }}>{threatScore}</span>
                  <span className="text-[8px] uppercase font-bold text-zinc-500">{getThreatLabel(threatScore)}</span>
                </div>
              </div>
            </div>

            {/* Map */}
            {session.geo && (
              <div className="glass rounded-2xl overflow-hidden">
                <div className="p-1">
                  <Map geoData={[{ session_id: session.session_id, client_ip: session.client_ip, username: session.username, geo: session.geo }]} />
                </div>
              </div>
            )}
          </div>

          {/* Center — Terminal View */}
          <div className="lg:col-span-6 space-y-4">
            <div className="glass rounded-2xl overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800/30 bg-zinc-900/30">
                <div className="flex gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-red-500/80" />
                  <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
                  <span className="w-3 h-3 rounded-full bg-green-500/80" />
                </div>
                <span className="text-xs font-mono text-zinc-500">{session.username}@aeroghost — {commands.length} commands</span>
              </div>
              <div className="bg-[#0c0c0c] p-4 font-mono text-sm h-[400px] overflow-y-auto">
                {commands.map((cmd, i) => (
                  <div key={i} className="mb-2">
                    <div className="flex items-start">
                      <span className="text-zinc-600 mr-2 select-none whitespace-nowrap">{session.username}@aeroghost:~$</span>
                      <span className={`break-all ${DANGEROUS_KEYWORDS.some(kw => cmd.command.toLowerCase().includes(kw)) ? 'text-rose-400' : 'text-zinc-300'}`}>{cmd.command}</span>
                    </div>
                    {cmd.response && (
                      <pre className="text-zinc-600 text-xs whitespace-pre-wrap mt-0.5 max-h-20 overflow-hidden leading-relaxed">{String(cmd.response).substring(0, 400)}</pre>
                    )}
                  </div>
                ))}
                {commands.length === 0 && <p className="text-zinc-700 text-center py-8">No commands recorded yet.</p>}
              </div>
            </div>

            {/* Intent Flow */}
            {intents.length > 0 && (
              <div className="glass rounded-2xl p-5">
                <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-1.5">
                  <Crosshair className="w-3.5 h-3.5 text-orange-500" /> Attacker Intent Flow
                </h3>
                <div className="flex flex-wrap gap-1.5 items-center">
                  {intents.map((intent: any, i: number) => (
                    <span key={i} className="flex items-center">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold text-orange-400 bg-orange-500/10">
                        {(intent.intent_type || '').replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                      </span>
                      {i < intents.length - 1 && <ChevronRight className="w-3 h-3 text-zinc-700 mx-0.5" />}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column */}
          <div className="lg:col-span-3 space-y-4">
            {/* Alerts */}
            <div className="glass rounded-2xl overflow-hidden flex flex-col max-h-[350px]">
              <div className="p-4 border-b border-zinc-800/30">
                <h3 className="text-xs font-semibold text-white flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-rose-500" /> Threat Alerts</h3>
              </div>
              <div className="p-3 overflow-y-auto flex-1 space-y-1.5">
                {alerts.length === 0 ? (
                  <p className="text-zinc-600 text-xs text-center py-4">No alerts</p>
                ) : (
                  alerts.slice(0, 15).map((a: any, i: number) => (
                    <div key={i} className="bg-zinc-900/30 rounded-lg p-2 text-[10px]">
                      <div className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${a.severity === 'high' || a.severity === 'critical' ? 'bg-rose-500' : 'bg-amber-500'}`} />
                        <span className="text-zinc-300 font-medium capitalize truncate">{String(a.threat_type || '').replace(/_/g, ' ')}</span>
                      </div>
                      <p className="text-zinc-600 truncate mt-0.5">{a.details || '—'}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Canary Status */}
            {canaries.length > 0 && (
              <div className="glass rounded-2xl p-4">
                <h3 className="text-xs font-semibold text-white mb-2.5 flex items-center gap-1.5"><FileWarning className="w-3.5 h-3.5 text-amber-500" /> Canary Tripwires</h3>
                <div className="space-y-1.5">
                  {canaries.map((c: any) => (
                    <div key={c.id} className="flex items-center justify-between text-[10px]">
                      <code className="text-zinc-400 truncate mr-2">{c.filepath}</code>
                      <span className={`font-bold flex-shrink-0 ${c.triggered ? 'text-rose-400' : 'text-zinc-600'}`}>
                        {c.triggered ? 'HIT' : 'SET'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Session Meta */}
            <div className="glass rounded-2xl p-4 text-[11px]">
              <h3 className="text-xs font-semibold text-white mb-2.5">Session Metadata</h3>
              <div className="space-y-1.5 text-zinc-500">
                <p>Started: <span className="text-zinc-300">{new Date(session.start_time).toLocaleString()}</span></p>
                {session.end_time && <p>Ended: <span className="text-zinc-300">{new Date(session.end_time).toLocaleString()}</span></p>}
                <p>Classification: <span className="text-zinc-300">{session.classification || 'Analyzing...'}</span></p>
                <p>Commands: <span className="text-zinc-300">{commands.length}</span></p>
                <p>Intents: <span className="text-zinc-300">{intents.length}</span></p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
