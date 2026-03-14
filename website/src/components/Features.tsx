'use client';

import { Shield, Activity, Target, Network, Layers, Fingerprint } from 'lucide-react';
import { motion } from 'framer-motion';

const features = [
  {
    title: 'Autonomous AI Deception',
    description: 'Dynamic LLM-generated responses for raw CLI commands prevent static fingerprinting.',
    icon: Shield,
    span: 'md:col-span-2',
  },
  {
    title: 'Real-Time Geo-Intelligence',
    description: 'Live IP mapping, ISP lookups, and origin tracking embedded directly in the dashboard.',
    icon: Target,
    span: '',
  },
  {
    title: 'Dynamic Threat Scoring',
    description: 'Algorithmic calculation of attacker danger based on behavioral volume and payload severity.',
    icon: Activity,
    span: '',
  },
  {
    title: 'Live Endpoint Mocking',
    description: 'Intercepts internal API probes and proxies them to a live Requestly mock environment.',
    icon: Network,
    span: '',
  },
  {
    title: 'Multi-layered Breadcrumbs',
    description: 'Bait files, fake sudo escalation, and simulated MySQL sessions to keep attackers engaged.',
    icon: Layers,
    span: '',
  },
  {
    title: 'Attacker Profiling',
    description: 'Keystroke timing analysis and SSH client fingerprinting to categorize bot vs human actors.',
    icon: Fingerprint,
    span: 'md:col-span-2',
  },
];

export function Features() {
  return (
    <section id="features" className="py-24 relative">
      <div className="absolute inset-0 bg-grid-fine" />
      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-sm font-semibold text-blue-500 tracking-widest uppercase mb-3">Core Capabilities</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Enterprise-Grade Deception
          </h2>
          <p className="mt-4 text-zinc-400 leading-relaxed">
            AeroGhost moves beyond static honeypots, actively analyzing and adapting to inbound threats.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{ delay: index * 0.08, duration: 0.5, ease: 'easeOut' }}
                className={`glass rounded-2xl p-7 hover:bg-white/[0.04] transition-all duration-300 group cursor-default ${feature.span}`}
              >
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center mb-5 group-hover:bg-blue-500/15 transition-colors">
                  <Icon className="w-5 h-5 text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                <p className="text-sm text-zinc-400 leading-relaxed">{feature.description}</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

