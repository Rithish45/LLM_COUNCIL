import React, { useEffect, useRef } from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu, CheckCircle2, Clock, AlertTriangle, Layers } from 'lucide-react';
import { useCouncilStore } from '../store/councilStore';

export default function LiveAgentFeed() {
  const agentLogs = useCouncilStore((state) => state.agentLogs);
  const currentAgent = useCouncilStore((state) => state.currentAgent);
  const feedEndRef = useRef(null);

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [agentLogs, currentAgent]);

  // Group logs so Member A and Member B running concurrently render side by side
  const renderLogItems = () => {
    const items = [];
    let i = 0;

    while (i < agentLogs.length) {
      const current = agentLogs[i];
      const next = agentLogs[i + 1];

      // Check if Member A and Member B are paired together
      const isMemberA = current.agent === 'Council Member A';
      const isMemberB = next && next.agent === 'Council Member B';

      if (isMemberA && isMemberB) {
        items.push(
          <div key={`pair-${i}`} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AgentCard log={current} />
            <AgentCard log={next} />
          </div>
        );
        i += 2;
      } else {
        items.push(<AgentCard key={`log-${i}`} log={current} />);
        i += 1;
      }
    }
    return items;
  };

  return (
    <div className="space-y-4 my-6">
      <div className="flex items-center justify-between px-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-2">
          <Layers className="w-4 h-4 text-amber-400" />
          <span>Live Deliberation Feed</span>
        </h3>
        {currentAgent && (
          <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 px-3 py-1 rounded-full text-xs text-amber-300 animate-pulse font-medium">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>Agent Executing: {currentAgent}</span>
          </div>
        )}
      </div>

      <div className="space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar p-1">
        {agentLogs.length === 0 ? (
          <SpatialGlassPanel elevation="flat" className="p-12 text-center border-dashed">
            <Cpu className="w-10 h-10 text-zinc-600 mx-auto mb-3 opacity-40" />
            <p className="text-sm text-zinc-400 font-medium">Click "Run Council" above to initiate the 6-agent debate council...</p>
          </SpatialGlassPanel>
        ) : (
          renderLogItems()
        )}
        <div ref={feedEndRef} />
      </div>
    </div>
  );
}

function AgentCard({ log }) {
  const isRunning = log.status === 'running';
  const isSuccess = log.status === 'success';
  const isFallback = log.fallback_triggered;

  // Provider badges
  const getProviderBadge = (provider) => {
    if (provider === 'ollama') return <span className="bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-mono">Local Ollama</span>;
    if (provider === 'groq') return <span className="bg-amber-500/10 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded text-[10px] font-mono">Groq Cloud</span>;
    if (provider === 'gemini') return <span className="bg-blue-500/10 text-blue-300 border border-blue-500/30 px-2 py-0.5 rounded text-[10px] font-mono">Gemini Fallback</span>;
    return <span className="bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded text-[10px] font-mono">{provider || 'Cloud'}</span>;
  };

  return (
    <SpatialGlassPanel
      elevation={isRunning ? 'floating' : 'standard'}
      glow={isRunning ? 'amber' : 'none'}
      className="p-5"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/5">
        <div className="flex items-center gap-2.5">
          <div className={`w-2.5 h-2.5 rounded-full ${isRunning ? 'bg-amber-400 animate-ping' : isSuccess ? 'bg-emerald-400' : 'bg-rose-400'}`} />
          <h4 className="text-sm font-bold text-zinc-100">{log.agent}</h4>
          {getProviderBadge(log.provider)}
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-400 font-mono">
          {log.latency_ms && (
            <span className="flex items-center gap-1 bg-zinc-900/80 px-2 py-0.5 rounded border border-white/5">
              <Clock className="w-3 h-3 text-zinc-400" />
              {(log.latency_ms / 1000).toFixed(2)}s
            </span>
          )}
        </div>
      </div>

      {/* Model used badge */}
      <div className="flex items-center justify-between text-xs text-zinc-400 mb-3 font-mono">
        <span>Model: <strong className="text-zinc-200">{log.model || 'Auto'}</strong></span>
        {isFallback && (
          <span className="text-[10px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> Fallback Triggered
          </span>
        )}
      </div>

      {/* Output Content */}
      <div className="text-xs leading-relaxed text-zinc-300 font-normal bg-zinc-950/50 p-3.5 rounded-xl border border-white/5 max-h-60 overflow-y-auto custom-scrollbar">
        {isRunning ? (
          <div className="flex items-center gap-2 text-amber-400/80 font-mono">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span>Generating response...</span>
          </div>
        ) : (
          <p className="whitespace-pre-wrap">{log.content || 'No response returned.'}</p>
        )}
      </div>
    </SpatialGlassPanel>
  );
}
