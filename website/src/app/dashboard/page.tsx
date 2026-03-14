'use client';

import { useState } from 'react';
import { DashboardOverview } from '@/components/DashboardOverview';
import { LiveAlerts } from '@/components/LiveAlerts';
import { SessionTracker } from '@/components/SessionTracker';
import { LiveTerminal } from '@/components/LiveTerminal';
import { GeoIntelligence } from '@/components/GeoIntelligence';
import { Analytics } from '@/components/Analytics';
import { Intelligence } from '@/components/Intelligence';
import Link from 'next/link';
import { ArrowLeft, Shield, Terminal, Globe, BarChart3, Activity, Brain } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'terminal', label: 'Live Terminal', icon: Terminal },
    { id: 'intelligence', label: 'Intelligence', icon: Brain },
    { id: 'geo', label: 'Geo-Intelligence', icon: Globe },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <main className="min-h-screen bg-[#09090b] p-4 sm:p-6 lg:p-8">
      
      {/* Header */}
      <div className="max-w-[1400px] mx-auto mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-zinc-500 hover:text-white transition-colors glass p-2 rounded-xl">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
              <Shield className="w-6 h-6 text-blue-500" />
              Intelligence Center
            </h1>
            <p className="text-sm text-zinc-500 mt-0.5">Real-time threat monitoring</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 glass text-emerald-400 px-4 py-2 rounded-xl text-sm font-medium">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          Honeypot Live
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto space-y-6">
        
        {/* Tab Bar */}
        <div className="glass rounded-2xl p-1.5 flex gap-1 overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-xl transition-all whitespace-nowrap flex-1 sm:flex-none justify-center ${
                activeTab === tab.id
                  ? 'bg-white/10 text-white shadow-sm'
                  : 'text-zinc-500 hover:text-zinc-300 hover:bg-white/[0.03]'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <DashboardOverview />
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <SessionTracker />
                  </div>
                  <div className="lg:col-span-1">
                    <LiveAlerts />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'terminal' && <LiveTerminal />}
            {activeTab === 'intelligence' && <Intelligence />}
            {activeTab === 'geo' && <GeoIntelligence />}
            {activeTab === 'analytics' && <Analytics />}
          </motion.div>
        </AnimatePresence>
      </div>
    </main>
  );
}
