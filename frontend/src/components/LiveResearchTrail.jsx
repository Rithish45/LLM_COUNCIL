import React from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ExternalLink, Database, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { useCouncilStore } from '../store/councilStore';

export default function LiveResearchTrail() {
  const claimLedger = useCouncilStore((state) => state.claimLedger);
  const researchTrail = useCouncilStore((state) => state.researchTrail);

  return (
    <SpatialGlassPanel elevation="elevated" className="p-6 my-6 border-amber-500/20">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Search className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-100 flex items-center gap-2">
              <span>Live Research Trail</span>
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30">
                Grounder Engine
              </span>
            </h3>
            <p className="text-xs text-zinc-400">Real-time claim verification & source evidence retrieval</p>
          </div>
        </div>
        <span className="text-xs text-zinc-400 font-mono">
          {claimLedger.length} Claims Grounded
        </span>
      </div>

      <div className="space-y-4 max-h-[450px] overflow-y-auto custom-scrollbar pr-1">
        <AnimatePresence initial={false}>
          {claimLedger.length === 0 ? (
            <div className="text-center py-10 border border-dashed border-white/10 rounded-xl bg-zinc-900/30">
              <Database className="w-8 h-8 text-zinc-600 mx-auto mb-2 opacity-50" />
              <p className="text-xs text-zinc-400 font-medium">Research trail will populate when Fact Grounder runs web verification...</p>
            </div>
          ) : (
            claimLedger.map((c, idx) => {
              const hasSources = c.sources && c.sources.length > 0;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ type: 'spring', stiffness: 260, damping: 22 }}
                  className="p-4 rounded-xl bg-zinc-900/70 border border-white/10 relative overflow-hidden"
                >
                  {/* Claim Header */}
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        c.author === 'Council Member A'
                          ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}>
                        {c.author}
                      </span>
                      <span className="text-xs text-zinc-400 font-mono">Claim #{idx + 1}</span>
                    </div>
                    <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-white/5">
                      Confidence: {c.confidence_level}
                    </span>
                  </div>

                  {/* Target Claim Text */}
                  <p className="text-xs text-zinc-200 font-medium bg-zinc-950/60 p-2.5 rounded-lg border border-white/5 mb-3 italic">
                    "{c.claim}"
                  </p>

                  {/* Search Query Executed */}
                  <div className="flex items-center gap-2 text-[11px] text-zinc-400 mb-3 bg-zinc-900/90 px-3 py-1.5 rounded border border-white/5">
                    <RefreshCw className="w-3 h-3 text-amber-400 shrink-0" />
                    <span className="font-semibold text-zinc-300">Query Sent:</span>
                    <span className="font-mono text-amber-300/90 truncate">"{c.claim.slice(0, 70)}..."</span>
                    <span className="ml-auto text-[10px] text-zinc-400 bg-zinc-800 px-1.5 py-0.5 rounded">
                      Engine: Wikipedia API / DDG
                    </span>
                  </div>

                  {/* Evidence Candidates Pool */}
                  <div className="space-y-1.5 pl-2 border-l-2 border-amber-500/30">
                    <p className="text-[10px] font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                      <Database className="w-3 h-3 text-amber-400" />
                      <span>Retrieved Sources Pool ({c.sources ? c.sources.length : 0})</span>
                    </p>

                    {hasSources ? (
                      c.sources.map((src, sIdx) => (
                        <div
                          key={sIdx}
                          className="flex items-center justify-between p-2 rounded bg-zinc-950/40 border border-white/5 hover:border-amber-500/30 transition-colors text-xs"
                        >
                          <div className="truncate pr-2">
                            <span className="font-semibold text-zinc-200 block truncate">{src.title}</span>
                            <span className="text-[11px] text-zinc-400 block truncate">{src.snippet}</span>
                          </div>
                          {src.url && (
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noreferrer"
                              className="shrink-0 px-2 py-1 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 rounded border border-amber-500/30 flex items-center gap-1 text-[10px] font-mono transition-colors"
                            >
                              <span>Open</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="flex items-center gap-2 p-2 rounded bg-zinc-950/40 border border-white/5 text-xs text-zinc-400">
                        <AlertCircle className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                        <span>Zero external web evidence candidate sources found for this claim string.</span>
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })
          )}
        </AnimatePresence>
      </div>
    </SpatialGlassPanel>
  );
}
