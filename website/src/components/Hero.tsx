'use client';

import { ArrowRight, Terminal, ShieldAlert } from 'lucide-react';
import Link from 'next/link';
import { motion } from 'framer-motion';

export function Hero() {
  return (
    <div className="relative pt-32 pb-24 sm:pt-44 sm:pb-32 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 bg-dots opacity-40" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-blue-600/8 rounded-full blur-[120px]" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-indigo-600/6 rounded-full blur-[100px]" />
      
      <div className="relative max-w-5xl mx-auto px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass text-sm font-medium text-blue-400 mb-8"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
          </span>
          Next-Gen Honeypot System
        </motion.div>
        
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-5xl sm:text-7xl font-bold text-white tracking-tight mb-6 leading-[1.1]"
        >
          Autonomous{' '}
          <span className="text-gradient">Threat Intelligence</span>
        </motion.h1>
        
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="max-w-2xl mx-auto text-lg text-zinc-400 mb-10 leading-relaxed"
        >
          Deploy an intelligent, high-interaction honeypot that actively deceives attackers, 
          dynamically proxies API requests, and provides real-time geographic threat scoring.
        </motion.p>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-3 justify-center items-center"
        >
          <Link 
            href="/dashboard"
            className="inline-flex items-center gap-2 px-7 py-3.5 bg-white text-zinc-950 font-semibold rounded-xl hover:bg-zinc-100 transition-all hover:shadow-lg hover:shadow-white/10 w-full sm:w-auto justify-center"
          >
            Enter Dashboard
            <ArrowRight className="w-4 h-4" />
          </Link>
          <Link 
            href="#features"
            className="inline-flex items-center gap-2 px-7 py-3.5 glass hover:bg-white/10 text-white font-medium rounded-xl transition-all w-full sm:w-auto justify-center"
          >
            <Terminal className="w-4 h-4" />
            Explore Architecture
          </Link>
        </motion.div>
      </div>
    </div>
  );
}
