import React, { useState } from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { motion, AnimatePresence } from 'framer-motion';
import { Scale, ExternalLink, ChevronDown, ChevronUp, CheckCircle2, XCircle, HelpCircle, AlertTriangle } from 'lucide-react';
import { useCouncilStore } from '../store/councilStore';

const verdictConfig = {
  strongly_supported: { label: 'Strongly Supported', color: 'text-emerald-300', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', icon: CheckCircle2 },
  strongly_supported_rebuttal_bonus: { label: 'Supported + Rebuttal', color: 'text-emerald-300', bg: 'bg-emerald-500/15', border: 'border-emerald-500/30', icon: CheckCircle2 },
  partially_supported: { label: 'Partially Supported', color: 'text-amber-300', bg: 'bg-amber-500/15', border: 'border-amber-500/30', icon: CheckCircle2 },
  partially_supported_rebuttal_bonus: { label: 'Partial + Rebuttal', color: 'text-amber-300', bg: 'bg-amber-500/15', border: 'border-amber-500/30', icon: CheckCircle2 },
  unverifiable: { label: 'Unverifiable', color: 'text-zinc-400', bg: 'bg-zinc-700/30', border: 'border-zinc-600/30', icon: HelpCircle },
  honest_uncertainty: { label: 'Honest Uncertainty', color: 'text-zinc-400', bg: 'bg-zinc-700/30', border: 'border-zinc-600/30', icon: HelpCircle },
  hedged_wrong: { label: 'Hedged Wrong', color: 'text-rose-300', bg: 'bg-rose-500/15', border: 'border-rose-500/30', icon: AlertTriangle },
  confident_wrong: { label: 'Confident Wrong', color: 'text-rose-300', bg: 'bg-rose-500/15', border: 'border-rose-500/30', icon: XCircle },
  wrong_doubled_down: { label: 'Doubled Down Wrong', color: 'text-rose-400', bg: 'bg-rose-500/20', border: 'border-rose-500/40', icon: XCircle },
};

function getVerdictStyle(verdict) {
  return verdictConfig[verdict] || verdictConfig.unverifiable;
}

export default function ClaimLedger() {
  const claimLedger = useCouncilStore((state) => state.claimLedger);
  const [expandedIdx, setExpandedIdx] = useState(null);

  const toggleExpand = (idx) => {
    setExpandedIdx(expandedIdx === idx ? null : idx);
  };

  return (
    <SpatialGlassPanel elevation="standard" className="p-6 my-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-100">Claim & Source Ledger</h3>
            <p className="text-xs text-zinc-400">Scored verdicts with evidence attribution</p>
          </div>
        </div>
        <span className="text-xs text-zinc-400 font-mono">{claimLedger.length} claims scored</span>
      </div>

      <div className="space-y-2.5 max-h-[500px] overflow-y-auto custom-scrollbar pr-1">
        <AnimatePresence initial={false}>
          {claimLedger.length === 0 ? (
            <div className="text-center py-10 border border-dashed border-white/10 rounded-xl bg-zinc-900/30">
              <Scale className="w-8 h-8 text-zinc-600 mx-auto mb-2 opacity-50" />
              <p className="text-xs text-zinc-400 font-medium">Claims will appear as the Fact Grounder evaluates council member arguments...</p>
            </div>
          ) : (
            claimLedger.map((c, idx) => {
              const style = getVerdictStyle(c.verdict);
              const VerdictIcon = style.icon;
              const isExpanded = expandedIdx === idx;
              const hasSources = c.sources && c.sources.length > 0;

              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ type: 'spring', stiffness: 280, damping: 24 }}
                >
                  <div
                    className="p-3.5 rounded-xl bg-zinc-900/60 border border-white/8 hover:border-white/15 transition-colors cursor-pointer"
                    onClick={() => toggleExpand(idx)}
                  >
                    {/* Top Row: Author, Verdict Badge, Points */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                          c.author === 'Council Member A'
                            ? 'bg-blue-500/15 text-blue-300 border border-blue-500/25'
                            : 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/25'
                        }`}>
                          {c.author === 'Council Member A' ? 'Member A' : 'Member B'}
                        </span>
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${style.bg} ${style.color} ${style.border} border flex items-center gap-1`}>
                          <VerdictIcon className="w-3 h-3" />
                          {style.label}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <motion.span
                          key={c.points}
                          initial={{ scale: 1.4, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          transition={{ type: 'spring', stiffness: 400, damping: 15 }}
                          className={`text-sm font-bold font-mono ${
                            c.points > 0 ? 'text-emerald-400' : c.points < 0 ? 'text-rose-400' : 'text-zinc-400'
                          }`}
                        >
                          {c.points > 0 ? `+${c.points}` : c.points}
                        </motion.span>
                        {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-zinc-400" /> : <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />}
                      </div>
                    </div>

                    {/* Claim Text */}
                    <p className="text-xs text-zinc-300 leading-relaxed italic line-clamp-2">"{c.claim}"</p>

                    {/* Expanded Details */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-3 pt-3 border-t border-white/5 space-y-2.5">
                            {/* Reasoning */}
                            <div>
                              <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 block mb-1">Reasoning</span>
                              <p className="text-xs text-zinc-400 leading-relaxed">{c.reasoning || 'No reasoning provided.'}</p>
                            </div>

                            {/* Sources */}
                            <div>
                              <span className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 block mb-1">
                                Sources ({c.sources ? c.sources.length : 0})
                              </span>
                              {hasSources ? (
                                <div className="space-y-1.5">
                                  {c.sources.map((src, sIdx) => (
                                    <a
                                      key={sIdx}
                                      href={src.url}
                                      target="_blank"
                                      rel="noreferrer"
                                      onClick={(e) => e.stopPropagation()}
                                      className="flex items-center justify-between p-2 rounded-lg bg-zinc-950/50 border border-white/5 hover:border-amber-500/30 transition-colors group"
                                    >
                                      <div className="truncate pr-2">
                                        <span className="text-xs font-medium text-zinc-200 block truncate">{src.title}</span>
                                        <span className="text-[10px] text-amber-400/70 font-mono block truncate">{src.url}</span>
                                      </div>
                                      <ExternalLink className="w-3.5 h-3.5 text-zinc-500 group-hover:text-amber-400 transition-colors shrink-0" />
                                    </a>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-xs text-zinc-500 italic">No external web sources found for this claim.</p>
                              )}
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
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
