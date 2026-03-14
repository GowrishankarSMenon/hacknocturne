'use client';

import { useState, useEffect } from 'react';
import { Activity, ShieldAlert, Monitor, Users } from 'lucide-react';
import { motion } from 'framer-motion';

interface Stats {
  total_sessions: number;
  active_sessions: number;
  unique_attacker_ips: number;
  total_alerts: number;
}

export function Metrics() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/stats');
        const data = await res.json();
        setStats(data);
      } catch (e) {
        // API not available — show placeholder
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const cards = [
    { title: 'Total Sessions', value: stats?.total_sessions ?? '—', icon: Monitor, color: 'text-blue-400', accent: 'bg-blue-500/10' },
    { title: 'Active Intruders', value: stats?.active_sessions ?? '—', icon: Activity, color: 'text-emerald-400', accent: 'bg-emerald-500/10' },
    { title: 'Unique IPs', value: stats?.unique_attacker_ips ?? '—', icon: Users, color: 'text-violet-400', accent: 'bg-violet-500/10' },
    { title: 'Threat Alerts', value: stats?.total_alerts ?? '—', icon: ShieldAlert, color: 'text-rose-400', accent: 'bg-rose-500/10' },
  ];

  return (
    <section className="py-20">
      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-4"
        >
          {cards.map((card, i) => (
            <div key={i} className="glass rounded-2xl p-6 flex items-center gap-4">
              <div className={`w-11 h-11 rounded-xl ${card.accent} flex items-center justify-center flex-shrink-0`}>
                <card.icon className={`w-5 h-5 ${card.color}`} />
              </div>
              <div>
                <p className="text-xs text-zinc-500 font-medium uppercase tracking-wider">{card.title}</p>
                <p className="text-2xl font-bold text-white mt-0.5">{card.value}</p>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
