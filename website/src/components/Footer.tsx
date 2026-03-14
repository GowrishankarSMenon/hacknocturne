'use client';

import { Github, Twitter, Linkedin } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-black py-12 border-t border-zinc-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-between md:flex-row">
        <div className="flex items-center gap-2 mb-4 md:mb-0">
          <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center font-bold text-white">
            AG
          </div>
          <span className="text-xl font-bold text-white tracking-tight">AeroGhost</span>
        </div>
        
        <p className="text-zinc-500 text-sm">
          Built for HackNocturne Data Security Hackathon.
        </p>

        <div className="flex gap-4 mt-6 md:mt-0">
          <a href="https://github.com/GowrishankarSMenon/hacknocturne" target="_blank" rel="noopener noreferrer" className="text-zinc-500 hover:text-white transition-colors">
            <span className="sr-only">GitHub</span>
            <Github className="w-5 h-5" />
          </a>
          <a href="#" className="text-zinc-500 hover:text-white transition-colors">
            <span className="sr-only">Twitter</span>
            <Twitter className="w-5 h-5" />
          </a>
          <a href="#" className="text-zinc-500 hover:text-white transition-colors">
            <span className="sr-only">LinkedIn</span>
            <Linkedin className="w-5 h-5" />
          </a>
        </div>
      </div>
    </footer>
  );
}
