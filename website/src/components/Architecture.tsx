'use client';

import { Server, ArrowRight, Database, MonitorPlay } from 'lucide-react';

export function Architecture() {
  return (
    <section className="py-24 bg-zinc-900 border-t border-zinc-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
            How AeroGhost Works
          </h2>
          <p className="mt-4 text-xl text-zinc-400">
            A seamless integration between Python deception logic, Requestly mock servers, and a Python Streamlit intelligence layer.
          </p>
        </div>

        <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-4 relative mt-16">
          
          {/* Step 1 */}
          <div className="flex flex-col items-center z-10">
            <div className="w-20 h-20 bg-zinc-950 border-2 border-zinc-700 rounded-2xl flex items-center justify-center mb-4 text-white shadow-lg">
              <MonitorPlay className="w-8 h-8 text-red-400" />
            </div>
            <h4 className="font-bold text-white text-lg">1. Attacker Probes</h4>
            <p className="text-zinc-400 text-sm text-center max-w-[200px] mt-2">
              SSH connection established. Malicious actors scan the fake network.
            </p>
          </div>

          <ArrowRight className="hidden md:block w-8 h-8 text-zinc-600 animate-pulse" />
          <div className="md:hidden h-8 w-0.5 bg-zinc-600 animate-pulse my-2" />

          {/* Step 2 */}
          <div className="flex flex-col items-center z-10">
            <div className="w-20 h-20 bg-blue-600 border-2 border-blue-400 rounded-2xl flex items-center justify-center mb-4 text-white shadow-lg shadow-blue-500/20">
              <Server className="w-8 h-8" />
            </div>
            <h4 className="font-bold text-white text-lg">2. AeroGhost Engine</h4>
            <p className="text-zinc-400 text-sm text-center max-w-[200px] mt-2">
              Python intercepts commands. LLM generates dynamic responses. Requestly proxies API calls.
            </p>
          </div>

          <ArrowRight className="hidden md:block w-8 h-8 text-zinc-600 animate-pulse" />
          <div className="md:hidden h-8 w-0.5 bg-zinc-600 animate-pulse my-2" />

          {/* Step 3 */}
          <div className="flex flex-col items-center z-10">
             <div className="w-20 h-20 bg-zinc-950 border-2 border-zinc-700 rounded-2xl flex items-center justify-center mb-4 text-white shadow-lg">
              <Database className="w-8 h-8 text-indigo-400" />
            </div>
            <h4 className="font-bold text-white text-lg">3. Intelligence Dash</h4>
            <p className="text-zinc-400 text-sm text-center max-w-[200px] mt-2">
              Streamlit dashboard consumes sqlite logs in real-time, mapping threats instantly.
            </p>
          </div>

        </div>
      </div>
    </section>
  );
}
