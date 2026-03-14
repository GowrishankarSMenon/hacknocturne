'use client';

import { Github } from 'lucide-react';
import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t border-zinc-800/50 bg-[#09090b]">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-accent flex items-center justify-center font-bold text-white text-xs">AG</div>
            <span className="text-sm font-semibold text-white tracking-tight">AeroGhost</span>
          </div>
          
          <p className="text-zinc-500 text-sm">
            Built for HackNocturne Data Security Hackathon
          </p>

          <div className="flex items-center gap-4">
            <a href="https://github.com/GowrishankarSMenon/hacknocturne" target="_blank" rel="noopener noreferrer" className="text-zinc-500 hover:text-white transition-colors">
              <Github className="w-5 h-5" />
            </a>
            <Link href="/dashboard" className="text-sm text-zinc-400 hover:text-white transition-colors">
              Dashboard →
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
