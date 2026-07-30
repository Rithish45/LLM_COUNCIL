import React from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, ExternalLink, ShieldCheck } from 'lucide-react';
import { useCouncilStore } from '../store/councilStore';

export default function FinalVerdictPanel() {
  const decision = useCouncilStore((state) => state.decision);
  const finalAnswer = useCouncilStore((state) => state.finalAnswer);
  const claimLedger = useCouncilStore((state) => state.claimLedger);
  const memberAnswers = useCouncilStore((state) => state.memberAnswers);
  const isRunning = useCouncilStore((state) => state.isRunning);

  if (isRunning || !finalAnswer) return null;

  const isConverged = decision === 'converge';

  // Collect all unique real sources from the claim ledger
  const allSources = [];
  const seenUrls = new Set();
  claimLedger.forEach((c) => {
    if (c.sources) {
      c.sources.forEach((src) => {
        if (src.url && !seenUrls.has(src.url)) {
          seenUrls.add(src.url);
          allSources.push(src);
        }
      });
    }
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 22, delay: 0.3 }}
      className="my-8"
    >
      <SpatialGlassPanel
        elevation="elevated"
        glow={isConverged ? 'emerald' : 'rose'}
        className="p-6 md:p-8"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/10">
          <div className="flex items-center gap-3">
            {isConverged ? (
              <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            ) : (
              <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <AlertTriangle className="w-5 h-5" />
              </div>
            )}
            <div>
              <h2 className="text-lg font-black tracking-tight text-zinc-100">
                {isConverged ? 'Council Reached Consensus' : 'Council Escalated — No Consensus'}
              </h2>
              <p className="text-xs text-zinc-400 mt-0.5">
                {isConverged
                  ? 'Members converged on a unified position backed by verified evidence.'
                  : 'Fundamental disagreements remain. Both positions are presented side-by-side.'}
              </p>
            </div>
          </div>
          <span className={`text-xs font-bold uppercase tracking-wider px-3 py-1.5 rounded-full ${
            isConverged
              ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
              : 'bg-rose-500/15 text-rose-300 border border-rose-500/30'
          }`}>
            {isConverged ? 'Converged' : 'Escalated'}
          </span>
        </div>

        {/* Final Answer Content */}
        {isConverged ? (
          <div className="bg-zinc-950/50 p-5 rounded-xl border border-white/8">
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-300">Synthesized Final Answer</span>
            </div>
            <div className="text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap">{finalAnswer}</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-zinc-950/50 p-4 rounded-xl border border-blue-500/15">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                <span className="text-xs font-bold uppercase tracking-wider text-blue-300">Council Member A Position</span>
              </div>
              <div className="text-xs text-zinc-300 leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto custom-scrollbar">
                {memberAnswers["Council Member A"] || 'No response.'}
              </div>
            </div>
            <div className="bg-zinc-950/50 p-4 rounded-xl border border-emerald-500/15">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-300">Council Member B Position</span>
              </div>
              <div className="text-xs text-zinc-300 leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto custom-scrollbar">
                {memberAnswers["Council Member B"] || 'No response.'}
              </div>
            </div>

            {/* Chairman's explanation below both */}
            <div className="md:col-span-2 bg-zinc-950/40 p-4 rounded-xl border border-white/8">
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-400 block mb-2">Chairman's Escalation Summary</span>
              <div className="text-xs text-zinc-300 leading-relaxed whitespace-pre-wrap">{finalAnswer}</div>
            </div>
          </div>
        )}

        {/* Verified Sources */}
        {allSources.length > 0 && (
          <div className="mt-5 pt-4 border-t border-white/8">
            <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-2">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              <span>Verified Evidence Sources ({allSources.length})</span>
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {allSources.map((src, idx) => (
                <a
                  key={idx}
                  href={src.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/60 border border-white/5 hover:border-amber-500/30 transition-colors group"
                >
                  <div className="truncate pr-2">
                    <span className="text-xs font-medium text-zinc-200 block truncate">{src.title}</span>
                    <span className="text-[10px] text-amber-400/60 font-mono block truncate">{src.url}</span>
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 text-zinc-500 group-hover:text-amber-400 transition-colors shrink-0" />
                </a>
              ))}
            </div>
          </div>
        )}
      </SpatialGlassPanel>
    </motion.div>
  );
}
