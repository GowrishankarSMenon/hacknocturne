import { Hero } from '@/components/Hero';
import { Features } from '@/components/Features';
import { Metrics } from '@/components/Metrics';
import { Architecture } from '@/components/Architecture';
import { Footer } from '@/components/Footer';

export default function Home() {
  return (
    <main className="min-h-screen bg-zinc-950 selection:bg-blue-500/30">
      
      {/* Navigation Bar */}
      <nav className="fixed w-full z-50 bg-zinc-950/80 backdrop-blur-md border-b border-zinc-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center font-bold text-white">
              AG
            </div>
            <span className="text-xl font-bold text-white tracking-tight">AeroGhost</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="https://github.com/GowrishankarSMenon/hacknocturne" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">GitHub Repo</a>
          </div>
        </div>
      </nav>

      {/* Main Page Content */}
      <Hero />
      <Features />
      <Metrics />
      <Architecture />
      <Footer />
    </main>
  );
}
