import { DashboardOverview } from '@/components/DashboardOverview';
import { LiveAlerts } from '@/components/LiveAlerts';
import { SessionTracker } from '@/components/SessionTracker';
import Link from 'next/link';
import { ArrowLeft, Shield } from 'lucide-react';

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-zinc-950 selection:bg-blue-500/30 p-4 sm:p-6 lg:p-8">
      
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Link href="/" className="text-zinc-500 hover:text-white transition-colors bg-zinc-900 p-2 rounded-lg border border-zinc-800 hover:border-zinc-700">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-2">
              <Shield className="w-8 h-8 text-blue-500" />
              Intelligence Center
            </h1>
          </div>
          <p className="text-zinc-400 ml-14">Real-time threat monitoring and session analytics</p>
        </div>
        
        <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 text-green-400 px-4 py-2 rounded-lg text-sm font-bold">
          <span className="relative flex h-2 w-2 mr-2">
            <span className="absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          Honeypot Live
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Top Stats */}
        <DashboardOverview />

        {/* Main Split Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <SessionTracker />
          </div>
          <div className="lg:col-span-1">
            <LiveAlerts />
          </div>
        </div>
      </div>

    </main>
  );
}
