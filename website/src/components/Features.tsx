'use client';

import { Shield, Activity, Target, Network, Layers, Fingerprint } from 'lucide-react';

const features = [
  {
    title: 'Autonomous AI Deception',
    description: 'Dynamic LLM-generated responses for raw CLI commands prevent static fingerprinting.',
    icon: Shield,
  },
  {
    title: 'Real-Time Geo-Intelligence',
    description: 'Live IP mapping, ISP lookups, and origin tracking embedded directly in the dashboard.',
    icon: Target,
  },
  {
    title: 'Dynamic Threat Scoring',
    description: 'Algorithmic calculation of attacker danger based on behavioral volume and payload severity.',
    icon: Activity,
  },
  {
    title: 'Live Endpoint Mocking',
    description: 'Intercepts internal API probes and proxies them to a live Requestly mock environment.',
    icon: Network,
  },
  {
    title: 'Multi-layered Breadcrumbs',
    description: 'Bait files, fake sudo escalation, and simulated MySQL sessions to keep attackers engaged.',
    icon: Layers,
  },
  {
    title: 'Attacker Profiling',
    description: 'Keystroke timing analysis and SSH client fingerprinting to categorize bot vs human actors.',
    icon: Fingerprint,
  },
];

export function Features() {
  return (
    <section id="features" className="py-24 bg-zinc-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-semibold text-blue-500 tracking-wide uppercase">Core Capabilities</h2>
          <p className="mt-2 text-3xl font-extrabold text-white sm:text-4xl">
            Enterprise-Grade Deception
          </p>
          <p className="mt-4 text-xl text-zinc-400">
            AeroGhost moves beyond static honeypots, actively analyzing and adapting to inbound threats.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 hover:border-blue-500/50 transition-colors duration-300 group"
            >
              <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center mb-6 group-hover:bg-blue-500/20 transition-colors">
                <feature.icon className="w-6 h-6 text-blue-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
              <p className="text-zinc-400 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
