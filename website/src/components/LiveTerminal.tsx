'use client';

import { useState, useEffect, useRef } from 'react';
import { Terminal, Activity } from 'lucide-react';

interface TypingSession {
  session_id: string;
  client_ip: string;
  username: string;
  buffer: string;
  last_update: string;
  commands?: { command: string; response: string; timestamp: string }[];
}

export function LiveTerminal() {
  const [sessions, setSessions] = useState<TypingSession[]>([]);
  const terminalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [typeRes, sessRes] = await Promise.all([
          fetch('http://localhost:8000/api/live-typing'),
          fetch('http://localhost:8000/api/sessions?status=active'),
        ]);

        if (typeRes.ok && sessRes.ok) {
          const typeData = await typeRes.json();
          const sessData = await sessRes.json();
          const activeSessions: TypingSession[] = [];

          for (const session of sessData.sessions || []) {
            if (session.status !== 'active') continue;
            const typing = typeData[session.session_id];
            
            // Fetch recent commands
            let cmds: any[] = [];
            try {
              const cmdRes = await fetch(`http://localhost:8000/api/sessions/${session.session_id}/commands`);
              const cmdData = await cmdRes.json();
              cmds = (cmdData.commands || []).slice(-15);
            } catch {}

            activeSessions.push({
              session_id: session.session_id,
              client_ip: session.client_ip,
              username: session.username || 'root',
              buffer: typing?.buffer || '',
              last_update: typing?.last_update || '',
              commands: cmds,
            });
          }
          setSessions(activeSessions);
        }
      } catch (e) {
        console.error('Failed to fetch live typing', e);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  if (sessions.length === 0) {
    return (
      <div className="glass rounded-2xl p-12 flex flex-col items-center justify-center text-center">
        <Terminal className="w-10 h-10 text-zinc-600 mb-3" />
        <h3 className="text-base font-semibold text-white mb-1">Live Terminal</h3>
        <p className="text-sm text-zinc-500">No active sessions — waiting for an attacker to connect...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {sessions.map(session => (
        <div key={session.session_id} className="glass rounded-2xl overflow-hidden">
          {/* Terminal chrome bar */}
          <div className="flex items-center gap-3 px-4 py-3 border-b border-zinc-800/50 bg-zinc-900/30">
            <div className="flex gap-1.5">
              <span className="w-3 h-3 rounded-full bg-red-500/80" />
              <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <span className="w-3 h-3 rounded-full bg-green-500/80" />
            </div>
            <div className="flex-1 flex items-center gap-2">
              <span className="text-xs font-mono text-zinc-500">
                {session.username}@{session.client_ip}
              </span>
              <span className="ml-auto flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500" />
                </span>
                LIVE
              </span>
            </div>
          </div>

          {/* Terminal body — compact, scroll to bottom */}
          <div 
            ref={terminalRef}
            className="bg-[#0c0c0c] p-4 font-mono text-sm h-[320px] overflow-y-auto flex flex-col-reverse"
          >
            <div>
              {/* Live typing buffer — always at the bottom */}
              <div className="flex items-start mt-1">
                <span className="text-emerald-400 font-bold mr-2 select-none whitespace-nowrap">{session.username}@aeroghost:~$</span>
                <span className="text-blue-400 whitespace-pre-wrap break-all">{session.buffer}</span>
                <span className="text-emerald-400 animate-pulse">█</span>
              </div>

              {/* Recent commands — displayed above the live buffer */}
              {session.commands && [...session.commands].reverse().map((cmd, i) => (
                <div key={i} className="mb-2">
                  <div className="flex items-start">
                    <span className="text-zinc-600 mr-2 select-none whitespace-nowrap">{session.username}@aeroghost:~$</span>
                    <span className="text-zinc-300 break-all">{cmd.command}</span>
                  </div>
                  {cmd.response && (
                    <pre className="text-zinc-500 text-xs whitespace-pre-wrap ml-0 mt-0.5 max-h-24 overflow-hidden leading-relaxed">
                      {String(cmd.response).substring(0, 500)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
