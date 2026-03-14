'use client';

import { useState, useEffect, useMemo } from 'react';
import dynamic from 'next/dynamic';
import {
  Brain, Shield, Crosshair, Terminal, Network, Lock, MapPin,
  Activity, AlertTriangle, ShieldAlert, FileWarning, ChevronRight,
  Loader2, FileText, Globe
} from 'lucide-react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const Map = dynamic(() => import('./MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="h-[200px] w-full rounded-xl bg-zinc-900/50 animate-pulse flex items-center justify-center text-zinc-600">
      <Globe className="w-5 h-5 opacity-30" />
    </div>
  ),
});

interface Session {
  session_id: string;
  client_ip: string;
  username: string;
  status: string;
  start_time: string;
  client_software: string;
  password_used: string;
  client_port: number;
  classification: string;
  avg_ipd: number;
  threat_score: number;
  geo?: { city: string; country: string; isp: string; lat: number; lon: number };
}

interface Intent { id: number; timestamp: string; intent_type: string; confidence: number; trigger_command: string; }
interface Canary { id: number; filepath: string; intent: string; planted_at: string; triggered: number; triggered_at: string | null; }
interface Command { id: number; timestamp: string; command: string; response: string; execution_time_ms: number; }
interface ThreatEvent { id: number; timestamp: string; event_type: string; severity: string; data: string; details?: string; display_type?: string; }
interface RSAAlert { id: number; client_ip: string; alert_type: string; severity: string; similarity_score: number; details: any; timestamp: string; }

const DANGEROUS_KEYWORDS = [
  'sudo', 'su ', 'passwd', 'shadow', 'wget', 'curl', 'nc ', 'ncat',
  'nmap', 'chmod', 'rm -rf', 'rm -r', 'mkfifo', 'bash -i',
  '/etc/passwd', '/etc/shadow', '.ssh', 'id_rsa', 'authorized_keys',
  'iptables', 'crontab', 'base64', 'python -c', 'perl -e',
  'netcat', 'reverse', 'bind', 'exploit', 'payload',
];

const getIntentColor = (intent: string) => {
  const i = intent.toLowerCase();
  if (i.includes('credential')) return 'text-rose-400 bg-rose-500/10';
  if (i.includes('ssh_key')) return 'text-amber-400 bg-amber-500/10';
  if (i.includes('database')) return 'text-violet-400 bg-violet-500/10';
  if (i.includes('lateral')) return 'text-pink-400 bg-pink-500/10';
  if (i.includes('exfil')) return 'text-blue-400 bg-blue-500/10';
  return 'text-zinc-400 bg-zinc-800';
};

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

export function Intelligence() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('');
  const [commands, setCommands] = useState<Command[]>([]);
  const [intents, setIntents] = useState<Intent[]>([]);
  const [canaries, setCanaries] = useState<Canary[]>([]);
  const [threatEvents, setThreatEvents] = useState<ThreatEvent[]>([]);
  const [rsaAlerts, setRsaAlerts] = useState<RSAAlert[]>([]);
  const [report, setReport] = useState<string>('');
  const [reportLoading, setReportLoading] = useState(false);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/sessions?status=active');
        const data = await res.json();
        setSessions(data.sessions || []);
        if (data.sessions?.length > 0 && !selectedSessionId) {
          setSelectedSessionId(data.sessions[0].session_id);
        }
      } catch (e) { console.error('Failed to fetch sessions', e); }
    };
    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!selectedSessionId) return;
    const fetchDetails = async () => {
      try {
        const [cmdRes, intentRes, canaryRes, alertRes] = await Promise.all([
          fetch(`http://localhost:8000/api/sessions/${selectedSessionId}/commands`),
          fetch(`http://localhost:8000/api/sessions/${selectedSessionId}/intents`),
          fetch(`http://localhost:8000/api/sessions/${selectedSessionId}/canaries`),
          fetch('http://localhost:8000/api/alerts'),
        ]);
        setCommands((await cmdRes.json()).commands || []);
        setIntents((await intentRes.json()).intents || []);
        setCanaries((await canaryRes.json()).canaries || []);
        const alertData = await alertRes.json();
        const sessionAlerts = (alertData.alerts || [])
          .filter((a: any) => a.session_id === selectedSessionId)
          .map((a: any) => ({ ...a, display_type: String(a.threat_type || a.event_type || 'Unknown').split('_').join(' ') }));
        setThreatEvents(sessionAlerts);
      } catch (e) { console.error('Failed to fetch session details', e); }
    };
    fetchDetails();
    const interval = setInterval(fetchDetails, 3000);
    return () => clearInterval(interval);
  }, [selectedSessionId]);

  useEffect(() => {
    const fetchRSA = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/rsa-alerts');
        setRsaAlerts((await res.json()).alerts || []);
      } catch (e) { console.error('Failed to fetch RSA alerts', e); }
    };
    fetchRSA();
    const interval = setInterval(fetchRSA, 5000);
    return () => clearInterval(interval);
  }, []);

  const selectedSession = sessions.find(s => s.session_id === selectedSessionId);

  const threatScore = useMemo(() => {
    if (!commands.length) return selectedSession?.threat_score || 0;
    let score = Math.min(commands.length * 2, 20);
    let dangerous = 0;
    for (const cmd of commands) {
      if (DANGEROUS_KEYWORDS.some(kw => (cmd.command || '').toLowerCase().includes(kw))) dangerous++;
    }
    score += Math.min(dangerous * 10, 60);
    if (commands.length >= 10) score += 10;
    if (commands.length >= 20) score += 10;
    return Math.min(score, 100);
  }, [commands, selectedSession]);

  const giaWarnings = useMemo(() => threatEvents.filter(t => t.event_type === 'gia_warning' || t.display_type?.toLowerCase().includes('gia')), [threatEvents]);

  const botStatus = useMemo(() => {
    for (const ev of giaWarnings) {
      try {
        const data = typeof ev.data === 'string' ? JSON.parse(ev.data) : ev.data;
        if (data?.check === 'bot_detected') {
          const msg = (data.message || '').toLowerCase();
          return msg.includes('bot') ? 'BOT' : msg.includes('suspicious') ? 'SUSPICIOUS' : 'HUMAN';
        }
      } catch {}
    }
    return selectedSession?.classification === 'bot' ? 'BOT'
      : selectedSession?.classification === 'suspicious' ? 'SUSPICIOUS'
      : selectedSession?.classification === 'human' ? 'HUMAN' : 'UNKNOWN';
  }, [giaWarnings, selectedSession]);

  const timelineData = useMemo(() => {
    return commands.map(cmd => ({
      ...cmd,
      isDangerous: DANGEROUS_KEYWORDS.some(kw => cmd.command.toLowerCase().includes(kw)),
    }));
  }, [commands]);

  const handleGenerateReport = async () => {
    if (!selectedSessionId) return;
    setReportLoading(true);
    setReport('');
    try {
      const res = await fetch(`http://localhost:8000/api/sessions/${selectedSessionId}/report`, { method: 'POST' });
      const data = await res.json();
      setReport(res.ok ? (data.report || 'No report content returned.') : `Error: ${data.detail || 'Failed to generate report'}`);
    } catch { setReport('Error: Could not reach API server'); }
    finally { setReportLoading(false); }
  };

  if (!sessions.length) {
    return (
      <div className="glass rounded-2xl p-12 flex flex-col items-center justify-center text-center">
        <Brain className="w-10 h-10 text-zinc-600 mb-3" />
        <h3 className="text-base font-semibold text-white mb-1">Intelligence Center</h3>
        <p className="text-sm text-zinc-500">No active sessions — intelligence will populate when an attacker connects.</p>
      </div>
    );
  }

  const canariesTriggered = canaries.filter(c => c.triggered).length;

  return (
    <div className="space-y-4">

      {/* Session Selector */}
      <div className="glass rounded-2xl p-4 flex items-center gap-3">
        <Brain className="w-4 h-4 text-indigo-500" />
        <select
          value={selectedSessionId}
          onChange={(e) => { setSelectedSessionId(e.target.value); setReport(''); }}
          className="flex-1 bg-zinc-900/60 border border-zinc-700/50 rounded-xl px-4 py-2 text-white text-sm font-mono focus:outline-none focus:border-indigo-500/50 transition-colors"
        >
          {sessions.map(s => (
            <option key={s.session_id} value={s.session_id}>
              {s.client_ip} — {s.username}@aeroghost ({String(s.session_id || '').substring(0, 8)}...)
            </option>
          ))}
        </select>
      </div>

      {selectedSession && (
        <>
          {/* Metrics Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: 'Commands', value: commands.length, icon: Terminal, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
              { label: 'Intents', value: intents.length, icon: Crosshair, color: 'text-orange-400', bg: 'bg-orange-500/10' },
              { label: 'Canaries', value: canaries.length, icon: Shield, color: 'text-blue-400', bg: 'bg-blue-500/10' },
              { label: 'Triggered', value: canariesTriggered, icon: ShieldAlert, color: 'text-rose-400', bg: 'bg-rose-500/10' },
            ].map((m, i) => (
              <div key={i} className="glass rounded-xl p-4 flex items-center gap-3">
                <div className={`w-9 h-9 rounded-lg ${m.bg} flex items-center justify-center`}>
                  <m.icon className={`w-4 h-4 ${m.color}`} />
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 font-semibold uppercase tracking-wider">{m.label}</p>
                  <p className="text-xl font-bold text-white">{m.value}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Bento Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">

            {/* Profile + Score + Map — Left */}
            <div className="lg:col-span-4 space-y-4">
              <div className="glass rounded-2xl overflow-hidden">
                <div className="p-4 border-b border-zinc-800/30 flex justify-between items-center">
                  <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <Network className="w-3.5 h-3.5 text-blue-500" /> Attacker Profile
                  </h3>
                  <span className={`text-lg font-black ${threatScore >= 80 ? 'text-rose-500' : threatScore >= 60 ? 'text-orange-500' : threatScore >= 30 ? 'text-amber-500' : 'text-emerald-500'}`}>
                    {threatScore}
                  </span>
                </div>
                <div className="p-4 space-y-3 text-xs">
                  <div className="grid grid-cols-2 gap-3">
                    {[
                      { label: 'IP Address', value: selectedSession.client_ip, style: 'text-blue-400 font-mono' },
                      { label: 'SSH Client', value: selectedSession.client_software || '—', style: 'text-zinc-300 font-mono truncate' },
                      { label: 'Location', value: selectedSession.geo ? `${selectedSession.geo.city}, ${selectedSession.geo.country}` : 'Unknown', style: 'text-zinc-300' },
                      { label: 'Password', value: selectedSession.password_used || '***', style: 'text-orange-400 font-mono' },
                      { label: 'ISP', value: selectedSession.geo?.isp || 'Unknown', style: 'text-zinc-400' },
                      { label: 'Source Port', value: String(selectedSession.client_port || '—'), style: 'text-zinc-400 font-mono' },
                    ].map((field, i) => (
                      <div key={i}>
                        <p className="text-[9px] text-zinc-600 uppercase font-semibold mb-0.5">{field.label}</p>
                        <p className={`text-[11px] ${field.style}`}>{field.value}</p>
                      </div>
                    ))}
                  </div>
                  <div className="pt-2 border-t border-zinc-800/30">
                    <p className="text-[9px] text-zinc-600 uppercase font-semibold mb-1">Classification</p>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      botStatus === 'BOT' ? 'text-rose-400 bg-rose-500/10'
                      : botStatus === 'SUSPICIOUS' ? 'text-amber-400 bg-amber-500/10'
                      : botStatus === 'HUMAN' ? 'text-emerald-400 bg-emerald-500/10'
                      : 'text-zinc-400 bg-zinc-800'
                    }`}>{botStatus}</span>
                  </div>
                </div>
              </div>

              {/* Threat Score Gauge */}
              <div className="glass rounded-2xl p-5">
                <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-rose-500" /> Threat Score
                </h3>
                <div className="relative h-28 flex items-center justify-center">
                  <Doughnut
                    data={{
                      labels: ['Threat', 'Safe'],
                      datasets: [{
                        data: [Math.min(100, threatScore), Math.max(0, 100 - threatScore)],
                        backgroundColor: [getThreatColor(threatScore), '#18181b'],
                        borderWidth: 0, borderRadius: 2, circumference: 180, rotation: 270,
                      }]
                    }}
                    options={{ cutout: '80%', plugins: { tooltip: { enabled: false }, legend: { display: false } }, maintainAspectRatio: false }}
                  />
                  <div className="absolute inset-0 flex flex-col items-center justify-center mt-5">
                    <span className="text-2xl font-black" style={{ color: getThreatColor(threatScore) }}>{threatScore}</span>
                    <span className="text-[9px] uppercase font-bold text-zinc-500">{getThreatLabel(threatScore)}</span>
                  </div>
                </div>
              </div>

              {/* Map */}
              {selectedSession.geo && (
                <div className="glass rounded-2xl overflow-hidden">
                  <div className="p-4 border-b border-zinc-800/30">
                    <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
                      <Globe className="w-3.5 h-3.5 text-violet-500" /> Attacker Location
                    </h3>
                  </div>
                  <div className="p-1">
                    <Map geoData={[{ session_id: selectedSession.session_id, client_ip: selectedSession.client_ip, username: selectedSession.username, geo: selectedSession.geo }]} />
                  </div>
                </div>
              )}
            </div>

            {/* Middle Column */}
            <div className="lg:col-span-4 space-y-4">
              {/* Intent Progression */}
              {intents.length > 0 && (
                <div className="glass rounded-2xl p-5">
                  <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-1.5"><Crosshair className="w-3.5 h-3.5 text-orange-500" /> Intent Progression</h3>
                  <div className="flex flex-wrap gap-1.5 items-center">
                    {intents.map((intent, i) => (
                      <span key={intent.id} className="flex items-center">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${getIntentColor(intent.intent_type)}`}>
                          {intent.intent_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                        {i < intents.length - 1 && <ChevronRight className="w-3 h-3 text-zinc-700 mx-0.5" />}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Command Timeline */}
              <div className="glass rounded-2xl p-5">
                <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-1.5"><Terminal className="w-3.5 h-3.5 text-emerald-500" /> Command Timeline</h3>
                {timelineData.length === 0 ? (
                  <p className="text-zinc-600 text-xs text-center py-3">No commands yet.</p>
                ) : (
                  <div className="space-y-1.5 max-h-[350px] overflow-y-auto">
                    {timelineData.map(cmd => (
                      <div key={cmd.id} className={`flex items-start gap-2 text-[11px] p-2 rounded-lg ${cmd.isDangerous ? 'bg-rose-500/5 border border-rose-500/10' : 'bg-zinc-900/30'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full mt-1 flex-shrink-0 ${cmd.isDangerous ? 'bg-rose-500' : 'bg-emerald-500'}`} />
                        <code className="text-zinc-300 truncate flex-1">{cmd.command}</code>
                        <span className="text-zinc-600 whitespace-nowrap text-[9px]">{new Date(cmd.timestamp).toLocaleTimeString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Canary Status */}
              {canaries.length > 0 && (
                <div className="glass rounded-2xl p-5">
                  <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-1.5"><FileWarning className="w-3.5 h-3.5 text-amber-500" /> Canary Tripwires</h3>
                  <div className="space-y-1.5">
                    {canaries.map(c => (
                      <div key={c.id} className={`flex items-center justify-between p-2 rounded-lg text-[10px] ${c.triggered ? 'bg-rose-500/5 border border-rose-500/10' : 'bg-zinc-900/30'}`}>
                        <div className="flex items-center gap-2 min-w-0">
                          <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${c.triggered ? 'bg-rose-500 animate-pulse' : 'bg-zinc-600'}`} />
                          <code className="text-zinc-400 truncate">{c.filepath}</code>
                        </div>
                        <span className={`font-bold px-1.5 py-0.5 rounded-full flex-shrink-0 ${c.triggered ? 'text-rose-400 bg-rose-500/10' : 'text-zinc-600 bg-zinc-800'}`}>
                          {c.triggered ? 'TRIGGERED' : 'PLANTED'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column */}
            <div className="lg:col-span-4 space-y-4">
              {/* GIA Alerts */}
              <div className="glass rounded-2xl overflow-hidden flex flex-col max-h-[350px]">
                <div className="p-4 border-b border-zinc-800/30">
                  <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> GIA Alerts
                  </h3>
                </div>
                <div className="p-3 overflow-y-auto flex-1 space-y-2">
                  {giaWarnings.length === 0 ? (
                    <p className="text-zinc-600 text-xs text-center py-3">No GIA alerts.</p>
                  ) : (
                    giaWarnings.map(w => {
                      let data: any = {};
                      try { data = typeof w.data === 'string' ? JSON.parse(w.data) : w.data; } catch {}
                      const check = data?.check || 'unknown';
                      const message = data?.message || w.details || 'No details';
                      const color = check === 'bot_detected' ? '#d29922'
                        : check === 'suspicious_behavior' ? '#e3b341'
                        : check === 'realism_check_failed' ? '#da3633' : '#8b949e';
                      return (
                        <div key={w.id} className="p-3 rounded-lg text-[11px]" style={{ borderLeft: `2px solid ${color}`, background: `${color}08` }}>
                          <span className="font-semibold text-zinc-300 capitalize block mb-0.5">{check.replace(/_/g, ' ')}</span>
                          <p className="text-zinc-500">{message}</p>
                        </div>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Report Generator */}
              <div className="glass rounded-2xl p-5">
                <h3 className="text-xs font-semibold text-white mb-3 flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-indigo-500" /> Threat Report
                </h3>
                <button
                  onClick={handleGenerateReport}
                  disabled={reportLoading}
                  className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 transition-colors text-white text-xs font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {reportLoading ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Generating...</> : <><FileText className="w-3.5 h-3.5" /> Generate Report</>}
                </button>
                {report && (
                  <div className="mt-3 bg-zinc-900/50 border border-zinc-800/30 rounded-xl p-4 text-[11px] text-zinc-300 font-mono whitespace-pre-wrap max-h-[300px] overflow-y-auto leading-relaxed">
                    {report}
                  </div>
                )}
              </div>

              {/* Recent Commands */}
              <div className="glass rounded-2xl overflow-hidden flex flex-col max-h-[250px]">
                <div className="p-4 border-b border-zinc-800/30">
                  <h3 className="text-xs font-semibold text-white flex items-center gap-1.5"><Terminal className="w-3.5 h-3.5 text-emerald-500" /> Recent Commands</h3>
                </div>
                <div className="p-3 overflow-y-auto flex-1 space-y-1.5">
                  {commands.slice(-8).reverse().map(cmd => (
                    <div key={cmd.id} className="p-2 bg-zinc-900/30 rounded-lg text-[10px]">
                      <code className="text-emerald-400">$ {cmd.command}</code>
                      {cmd.response && (
                        <pre className="text-zinc-600 text-[9px] whitespace-pre-wrap mt-0.5 max-h-10 overflow-hidden">{String(cmd.response).substring(0, 150)}</pre>
                      )}
                    </div>
                  ))}
                  {commands.length === 0 && <p className="text-zinc-600 text-xs text-center py-3">No commands yet.</p>}
                </div>
              </div>
            </div>
          </div>

          {/* RSA Alerts — Full Width */}
          <div className="glass rounded-2xl overflow-hidden">
            <div className="p-5 border-b border-zinc-800/30 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-500" /> RSA & Fingerprint Alerts
              </h3>
              <span className="text-xs text-zinc-500">{rsaAlerts.length} alert{rsaAlerts.length !== 1 ? 's' : ''}</span>
            </div>
            <div className="p-4">
              {rsaAlerts.length === 0 ? (
                <p className="text-zinc-600 text-sm text-center py-6">No RSA Alerts — system is monitoring</p>
              ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  {rsaAlerts.map(alert => {
                    const details = typeof alert.details === 'object' ? alert.details : {};
                    const sevColor = { CRITICAL: 'text-rose-400 bg-rose-500/10', HIGH: 'text-orange-400 bg-orange-500/10', MEDIUM: 'text-amber-400 bg-amber-500/10', LOW: 'text-emerald-400 bg-emerald-500/10' }[alert.severity] || 'text-zinc-400 bg-zinc-800';
                    return (
                      <div key={alert.id} className="bg-zinc-900/40 rounded-xl p-4 border border-zinc-800/20">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="text-xs text-white font-semibold flex items-center gap-1.5">
                            ⚠️ {alert.alert_type.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                            <span className="text-zinc-500 font-mono text-[10px]">{alert.client_ip}</span>
                          </h4>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${sevColor}`}>{alert.severity}</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 mb-2">
                          {[
                            { label: 'Similarity', value: `${alert.similarity_score}/100` },
                            { label: 'Connections', value: details.connections_in_window || '?' },
                            { label: 'Severity', value: alert.severity },
                          ].map((stat, j) => (
                            <div key={j} className="bg-zinc-900/60 p-2 rounded-lg text-center">
                              <p className="text-[8px] text-zinc-600 uppercase font-semibold">{stat.label}</p>
                              <p className="text-sm font-bold text-white">{stat.value}</p>
                            </div>
                          ))}
                        </div>
                        {details.hassh_values && details.hassh_values.length > 0 && (
                          <p className="text-[10px] text-zinc-500">
                            <span className="text-zinc-400 font-semibold">HASSH:</span> {details.hassh_values.map((h: string | null) => String(h || '').substring(0, 16) + '...').join(', ')}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
