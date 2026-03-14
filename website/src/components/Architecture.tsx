'use client';

import { Server, Database, MonitorPlay } from 'lucide-react';
import { motion } from 'framer-motion';

const steps = [
  {
    title: 'Attacker Probes',
    description: 'SSH connection established. Malicious actors scan the fake network.',
    icon: MonitorPlay,
    accent: 'text-red-400 bg-red-500/10',
  },
  {
    title: 'AeroGhost Engine',
    description: 'Python intercepts commands. LLM generates dynamic responses. Requestly proxies API calls.',
    icon: Server,
    accent: 'text-blue-400 bg-blue-500/10',
    highlight: true,
  },
  {
    title: 'Intelligence Dash',
    description: 'Next.js dashboard consumes sqlite logs in real-time, mapping threats instantly.',
    icon: Database,
    accent: 'text-indigo-400 bg-indigo-500/10',
  },
];

export function Architecture() {
  return (
    <section id="architecture" className="py-24 bg-zinc-950/50 border-t border-zinc-800/50">
      <div className="max-w-5xl mx-auto px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            How AeroGhost Works
          </h2>
          <p className="mt-4 text-zinc-400 leading-relaxed">
            A seamless pipeline between Python deception logic, Requestly mock servers, and a real-time intelligence layer.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15, duration: 0.5 }}
              className={`glass rounded-2xl p-7 text-center relative group hover:bg-white/[0.04] transition-all ${step.highlight ? 'glow-border' : ''}`}
            >
              <div className="flex justify-center mb-5">
                <div className={`w-14 h-14 rounded-2xl ${step.accent} flex items-center justify-center`}>
                  <step.icon className="w-7 h-7" />
                </div>
              </div>
              <div className="text-xs font-bold text-zinc-500 uppercase tracking-widest mb-2">Step {i + 1}</div>
              <h4 className="text-lg font-semibold text-white mb-2">{step.title}</h4>
              <p className="text-sm text-zinc-400 leading-relaxed">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
