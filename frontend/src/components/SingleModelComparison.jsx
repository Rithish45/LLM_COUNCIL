import React from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { motion } from 'framer-motion';
import { Columns2, ShieldCheck, Scale } from 'lucide-react';
import { useCouncilStore } from '../store/councilStore';

export default function SingleModelComparison() {
  const compareSingleModel = useCouncilStore((state) => state.compareSingleModel);
  const singleModelAnswer = useCouncilStore((state) => state.singleModelAnswer);
  const finalAnswer = useCouncilStore((state) => state.finalAnswer);
  const claimLedger = useCouncilStore((state) => state.claimLedger);
  const memberScores = useCouncilStore((state) => state.memberScores);
  const isRunning = useCouncilStore((state) => state.isRunning);

  if (!compareSingleModel || isRunning || !finalAnswer) return null;

  const totalClaims = claimLedger.length;
  const verifiedClaims = claimLedger.filter(c => c.points > 0).length;
  const sourceCount = new Set(claimLedger.flatMap(c => (c.source_urls || []).filter(Boolean))).size;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 200, damping: 22, delay: 0.5 }}
      className="my-8"
    >
      <SpatialGlassPanel elevation="elevated" className="p-6 md:p-8">
        <div className="flex items-center gap-2.5 mb-5 pb-4 border-b border-white/10">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Columns2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-100">
              Single-Model vs 6-Agent Council
            </h3>
            <p className="text-xs text-zinc-400">Side-by-side comparison — raw LLM output vs grounded council deliberation</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Single Model (Left) */}
          <div className="bg-zinc-950/50 p-5 rounded-xl border border-white/8 relative">
            <div className="absolute top-3 right-3">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-zinc-800/80 text-zinc-400 border border-white/5">
                Raw LLM
              </span>
            </div>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-2 h-2 rounded-full bg-zinc-500" />
              <span className="text-xs font-bold uppercase tracking-wider text-zinc-400">Single Model Answer</span>
            </div>
            <div className="text-xs text-zinc-300 leading-relaxed whitespace-pre-wrap max-h-80 overflow-y-auto custom-scrollbar mb-4">
              {singleModelAnswer || 'Single-model answer not available.'}
            </div>

            {/* Stats for single model */}
            <div className="pt-3 border-t border-white/5 flex items-center gap-4 text-[10px] text-zinc-500">
              <span>Claims verified: <strong className="text-zinc-400">0</strong></span>
              <span>Sources cited: <strong className="text-zinc-400">0</strong></span>
              <span>Fact-checked: <strong className="text-zinc-400">No</strong></span>
            </div>
          </div>

          {/* Council Result (Right) */}
          <div className="bg-zinc-950/50 p-5 rounded-xl border border-emerald-500/15 relative">
            <div className="absolute top-3 right-3">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/25">
                6-Agent Council
              </span>
            </div>
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-300">Council Verified Answer</span>
            </div>
            <div className="text-xs text-zinc-200 leading-relaxed whitespace-pre-wrap max-h-80 overflow-y-auto custom-scrollbar mb-4">
              {finalAnswer}
            </div>

            {/* Stats for council */}
            <div className="pt-3 border-t border-emerald-500/10 flex items-center gap-4 text-[10px] text-zinc-400">
              <span>Claims verified: <strong className="text-emerald-300">{verifiedClaims}/{totalClaims}</strong></span>
              <span>Sources cited: <strong className="text-emerald-300">{sourceCount}</strong></span>
              <span>Fact-checked: <strong className="text-emerald-300">Yes — live web grounding</strong></span>
            </div>
          </div>
        </div>
      </SpatialGlassPanel>
    </motion.div>
  );
}
