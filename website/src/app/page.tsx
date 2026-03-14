'use client';

import { Hero } from '@/components/Hero';
import { Features } from '@/components/Features';
import { Metrics } from '@/components/Metrics';
import { Architecture } from '@/components/Architecture';
import { Footer } from '@/components/Footer';
import Link from 'next/link';
import { useState, useEffect } from 'react';

export default function Home() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <main className="min-h-screen bg-[#09090b]">
      
      {/* Glassmorphism Navbar */}
      <nav className={`fixed w-full z-50 transition-all duration-300 ${scrolled ? 'glass-strong shadow-lg shadow-black/20' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-accent flex items-center justify-center font-bold text-white text-sm shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-shadow">
              AG
            </div>
            <span className="text-lg font-semibold text-white tracking-tight">AeroGhost</span>
          </Link>
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-zinc-400 hover:text-white transition-colors">Features</a>
            <a href="#architecture" className="text-sm text-zinc-400 hover:text-white transition-colors">Architecture</a>
            <a href="https://github.com/GowrishankarSMenon/hacknocturne" target="_blank" rel="noopener noreferrer" className="text-sm text-zinc-400 hover:text-white transition-colors">GitHub</a>
            <Link href="/dashboard" className="text-sm font-medium text-white bg-white/10 hover:bg-white/15 px-4 py-2 rounded-lg border border-white/10 transition-all">
              Dashboard →
            </Link>
          </div>
        </div>
      </nav>

      <Hero />
      <Features />
      <Metrics />
      <Architecture />
      <Footer />
    </main>
  );
}
