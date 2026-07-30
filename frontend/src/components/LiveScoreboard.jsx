import React from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { motion } from 'framer-motion';
import { Trophy } from 'lucide-react';
import { useCouncilStore } from '../store/councilStore';

function AnimatedScore({ value, label, color }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">{label}</span>
      <motion.span
        key={value}
        initial={{ scale: 1.5, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 400, damping: 15 }}
        className={`text-3xl font-black font-mono tabular-nums ${color}`}
      >
        {value}
      </motion.span>
    </div>
  );
}

export default function LiveScoreboard() {
  const memberScores = useCouncilStore((state) => state.memberScores);
  const isRunning = useCouncilStore((state) => state.isRunning);

  const scoreA = memberScores["Council Member A"] || 0;
  const scoreB = memberScores["Council Member B"] || 0;
  const maxScore = Math.max(Math.abs(scoreA), Math.abs(scoreB), 1);

  // Bar widths as percentage of max
  const barA = Math.abs(scoreA) / (Math.abs(scoreA) + Math.abs(scoreB) + 0.001) * 100;
  const barB = 100 - barA;

  return (
    <SpatialGlassPanel elevation="elevated" interactive={false} className="p-5 sticky top-4 z-30">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Trophy className="w-4 h-4 text-amber-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-300">Live Scoreboard</h3>
        </div>
        {isRunning && (
          <span className="text-[10px] text-amber-300 bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-full animate-pulse font-medium">
            Scoring Live
          </span>
        )}
      </div>

      {/* Score Display */}
      <div className="flex items-center justify-between gap-6">
        <div className="flex-1 text-center">
          <div className="text-[10px] font-bold uppercase tracking-wider text-blue-300/80 mb-1">Member A</div>
          <div className="text-xs text-zinc-400 font-mono mb-2">qwen2.5:1.5b</div>
          <AnimatedScore value={scoreA} label="" color={scoreA >= 0 ? 'text-blue-300' : 'text-rose-400'} />
        </div>

        <div className="flex flex-col items-center gap-1">
          <span className="text-lg font-bold text-zinc-600">vs</span>
        </div>

        <div className="flex-1 text-center">
          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-300/80 mb-1">Member B</div>
          <div className="text-xs text-zinc-400 font-mono mb-2">gemma2:2b</div>
          <AnimatedScore value={scoreB} label="" color={scoreB >= 0 ? 'text-emerald-300' : 'text-rose-400'} />
        </div>
      </div>

      {/* Score Bar */}
      <div className="mt-4 h-2 rounded-full bg-zinc-900/80 overflow-hidden flex">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500/60 to-blue-400/40 rounded-l-full"
          animate={{ width: `${barA}%` }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
        />
        <motion.div
          className="h-full bg-gradient-to-r from-emerald-400/40 to-emerald-500/60 rounded-r-full"
          animate={{ width: `${barB}%` }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
        />
      </div>
    </SpatialGlassPanel>
  );
}
