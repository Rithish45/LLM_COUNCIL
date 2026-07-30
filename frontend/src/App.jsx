import React, { useRef, useCallback, useEffect } from 'react';
import { useCouncilStore } from './store/councilStore';

// Components
import AmbientBackground from './components/AmbientBackground';
import QuestionInput from './components/QuestionInput';
import LiveScoreboard from './components/LiveScoreboard';
import LiveAgentFeed from './components/LiveAgentFeed';
import LiveResearchTrail from './components/LiveResearchTrail';
import ClaimLedger from './components/ClaimLedger';
import DisagreementChart from './components/DisagreementChart';
import FinalVerdictPanel from './components/FinalVerdictPanel';
import SingleModelComparison from './components/SingleModelComparison';
import RoundNavigator from './components/RoundNavigator';

import { Sparkles, ShieldCheck, Cpu, Globe } from 'lucide-react';

const API_BASE = 'http://localhost:8001';
const WS_BASE = 'ws://localhost:8001';

export default function App() {
  const socketRef = useRef(null);
  const reconnectTimer = useRef(null);
  const startRun = useCouncilStore((state) => state.startRun);
  const updateFromWebSocket = useCouncilStore((state) => state.updateFromWebSocket);
  const isRunning = useCouncilStore((state) => state.isRunning);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (socketRef.current) socketRef.current.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, []);

  const connectWebSocket = useCallback((requestId) => {
    const wsUrl = `${WS_BASE}/ws/council/${requestId}`;
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log('[WS] Connected:', wsUrl);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        updateFromWebSocket(msg);
      } catch (e) {
        console.warn('[WS] Parse error:', e);
      }
    };

    ws.onerror = (err) => {
      console.error('[WS] Error:', err);
    };

    ws.onclose = (event) => {
      console.log('[WS] Closed:', event.code, event.reason);
      // Auto-reconnect if still running
      if (useCouncilStore.getState().isRunning) {
        reconnectTimer.current = setTimeout(() => {
          console.log('[WS] Reconnecting...');
          connectWebSocket(requestId);
        }, 2000);
      }
    };
  }, [updateFromWebSocket]);

  const handleStartCouncil = useCallback(async (question) => {
    try {
      const res = await fetch(`${API_BASE}/api/council/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data = await res.json();
      const requestId = data.request_id;

      startRun(requestId, question);
      connectWebSocket(requestId);
    } catch (err) {
      console.error('[API] Failed to start council run:', err);
    }
  }, [startRun, connectWebSocket]);

  return (
    <div className="relative min-h-screen">
      <AmbientBackground />

      <div className="relative z-10 max-w-7xl mx-auto px-4 md:px-6 lg:px-8 pb-20">
        {/* Header */}
        <header className="pt-10 pb-6 text-center">
          <div className="flex items-center justify-center gap-3 mb-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-[0_0_20px_rgba(245,158,11,0.15)]">
              <ShieldCheck className="w-6 h-6" />
            </div>
          </div>
          <h1 className="text-3xl md:text-4xl font-black tracking-tight text-zinc-100 mb-2">
            LLM Council
          </h1>
          <p className="text-sm text-zinc-400 max-w-xl mx-auto leading-relaxed">
            6-agent adversarial deliberation with live web-grounded fact checking, multi-round debate scoring, and transparent research provenance.
          </p>

          {/* Feature badges */}
          <div className="flex flex-wrap items-center justify-center gap-3 mt-4">
            {[
              { icon: Cpu, label: '4 Local Models', detail: 'Ollama' },
              { icon: Globe, label: 'Live Web Grounding', detail: 'Wikipedia + DDG' },
              { icon: Sparkles, label: 'Cloud Fallback', detail: 'Groq + Gemini' },
            ].map((badge, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-900/50 border border-white/5 text-xs text-zinc-400"
              >
                <badge.icon className="w-3.5 h-3.5 text-amber-400/70" />
                <span className="font-medium text-zinc-300">{badge.label}</span>
                <span className="text-zinc-500">·</span>
                <span className="font-mono text-[10px] text-zinc-500">{badge.detail}</span>
              </div>
            ))}
          </div>
        </header>

        {/* Question Input */}
        <QuestionInput onSubmit={handleStartCouncil} />

        {/* Round Navigator */}
        <RoundNavigator />

        {/* Main Content Layout: 2-column on desktop */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 mt-6">
          {/* Left Column: Deliberation Feed + Research Trail */}
          <div className="lg:col-span-8 space-y-0">
            <LiveAgentFeed />
            <LiveResearchTrail />
          </div>

          {/* Right Column: Scoreboard + Claim Ledger + Chart */}
          <div className="lg:col-span-4 space-y-6">
            <LiveScoreboard />
            <ClaimLedger />
            <DisagreementChart />
          </div>
        </div>

        {/* Full-width sections below */}
        <FinalVerdictPanel />
        <SingleModelComparison />
      </div>
    </div>
  );
}
