'use client';

import { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Monitor, Users } from 'lucide-react';

interface Stats {
  total_sessions: number;
  active_sessions: number;
  unique_attacker_ips: number;
  total_alerts: number;
}

export function DashboardOverview() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/stats');
        const data = await res.json();
        setStats(data);
      } catch (e) {
        console.error("Failed to fetch stats", e);
      }
    };
    
    fetchStats();
    const interval = setInterval(fetchStats, 3000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return <div className="animate-pulse bg-zinc-900 h-32 rounded-xl" />;

  const cards = [
    { title: 'Total Sessions', value: stats.total_sessions, icon: Monitor, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { title: 'Active Intruders', value: stats.active_sessions, icon: Activity, color: 'text-green-500', bg: 'bg-green-500/10' },
    { title: 'Unique IPs', value: stats.unique_attacker_ips, icon: Users, color: 'text-purple-500', bg: 'bg-purple-500/10' },
    { title: 'Threat Alerts', value: stats.total_alerts, icon: ShieldAlert, color: 'text-red-500', bg: 'bg-red-500/10' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, i) => (
        <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex items-center justify-between">
          <div>
            <p className="text-zinc-400 text-sm font-medium">{card.title}</p>
            <p className="text-3xl font-bold text-white mt-1">{card.value}</p>
          </div>
          <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${card.bg}`}>
            <card.icon className={`w-6 h-6 ${card.color}`} />
          </div>
        </div>
      ))}
    </div>
  );
}
