'use client';

import { ArrowRight, Terminal, ShieldAlert } from 'lucide-react';
import Link from 'next/link';

export function Hero() {
  return (
    <div className="relative pt-32 pb-20 sm:pt-40 sm:pb-24 overflow-hidden bg-zinc-950">
      <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-10" />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium mb-8">
          <ShieldAlert className="w-4 h-4" />
          <span>Next-Gen Honeypot System</span>
        </div>
        
        <h1 className="text-5xl sm:text-7xl font-extrabold text-white tracking-tight mb-8">
          AeroGhost: Autonomous <br className="hidden sm:block" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">
            Threat Intelligence
          </span>
        </h1>
        
        <p className="max-w-2xl mx-auto text-xl text-zinc-400 mb-10 leading-relaxed">
          Deploy an intelligent, high-interaction honeypot that actively deceives attackers, 
          dynamically proxies API requests, and provides real-time geographic threat scoring.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link 
            href="/dashboard"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-zinc-950 font-bold rounded-lg hover:bg-zinc-200 transition-colors w-full sm:w-auto justify-center"
          >
            Enter Dashboard
            <ArrowRight className="w-5 h-5" />
          </Link>
          <Link 
            href="#features"
            className="inline-flex items-center gap-2 px-8 py-4 bg-zinc-900 border border-zinc-800 text-white font-medium rounded-lg hover:border-zinc-700 transition-colors w-full sm:w-auto justify-center"
          >
            <Terminal className="w-5 h-5" />
            Explore Architecture
          </Link>
        </div>
      </div>
    </div>
  );
}
