'use client';

import { BarChart3, LineChart, Map } from 'lucide-react';

export function Metrics() {
  return (
    <section className="py-24 bg-zinc-950 border-t border-zinc-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col lg:flex-row gap-16 items-center">
          
          <div className="flex-1 space-y-8">
            <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
              Understand the <span className="text-blue-500">Threat Landscape</span>
            </h2>
            <p className="text-xl text-zinc-400 leading-relaxed">
              AeroGhost doesn&apos;t just log commands; it analyzes intent. 
              Our intelligence dashboard transforms raw SSH sessions into actionable security metrics.
            </p>
            
            <ul className="space-y-6">
              <li className="flex gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-zinc-900 border border-zinc-800 rounded-lg flex items-center justify-center">
                  <Map className="w-6 h-6 text-blue-400" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-white">Global Heatmaps</h4>
                  <p className="text-zinc-400 mt-1">Visualize attacker origins globally with live IP tracking.</p>
                </div>
              </li>
              <li className="flex gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-zinc-900 border border-zinc-800 rounded-lg flex items-center justify-center">
                  <LineChart className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-white">Temporal Analysis</h4>
                  <p className="text-zinc-400 mt-1">Spot reconnaissance bursts and automated bot behavior over 24-hour periods.</p>
                </div>
              </li>
              <li className="flex gap-4">
                <div className="flex-shrink-0 w-12 h-12 bg-zinc-900 border border-zinc-800 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-6 h-6 text-purple-400" />
                </div>
                <div>
                  <h4 className="text-lg font-bold text-white">Severity Gauging</h4>
                  <p className="text-zinc-400 mt-1">Instantly know if a session is low-risk exploration or a high-risk extraction attempt.</p>
                </div>
              </li>
            </ul>
          </div>

          <div className="flex-1 w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl -mr-16 -mt-16 transition-opacity group-hover:bg-blue-500/20" />
            <div className="relative z-10 flex flex-col gap-4">
               {/* Abstract Mockup of Dashboard */}
               <div className="h-8 w-1/3 bg-zinc-800 rounded animate-pulse" />
               <div className="h-48 w-full bg-zinc-950 border border-zinc-800 rounded-lg flex items-end p-4 gap-2">
                  {[40, 70, 45, 90, 65, 30, 85].map((h, i) => (
                    <div key={i} className="flex-1 bg-gradient-to-t from-blue-600 to-indigo-400 rounded-t-sm" style={{ height: `${h}%` }} />
                  ))}
               </div>
               <div className="flex gap-4 mt-2">
                 <div className="h-24 flex-1 bg-zinc-800 rounded border border-zinc-700/50" />
                 <div className="h-24 flex-1 bg-zinc-800 rounded border border-zinc-700/50" />
               </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
