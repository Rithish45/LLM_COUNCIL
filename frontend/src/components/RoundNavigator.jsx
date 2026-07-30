import React from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { motion } from 'framer-motion';
import { useCouncilStore } from '../store/councilStore';

export default function RoundNavigator() {
  const maxRounds = useCouncilStore((state) => state.maxRounds);
  const roundNumber = useCouncilStore((state) => state.roundNumber);
  const activeRoundTab = useCouncilStore((state) => state.activeRoundTab);
  const setActiveRoundTab = useCouncilStore((state) => state.setActiveRoundTab);

  if (maxRounds <= 1) return null;

  const rounds = Array.from({ length: Math.max(roundNumber, maxRounds) }, (_, i) => i + 1);

  return (
    <SpatialGlassPanel elevation="flat" interactive={false} className="p-3 my-4 flex items-center gap-2 justify-center">
      <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-500 mr-2">Round:</span>
      {rounds.map((r) => {
        const isActive = r === activeRoundTab;
        const isCompleted = r < roundNumber;
        const isCurrent = r === roundNumber;

        return (
          <button
            key={r}
            onClick={() => setActiveRoundTab(r)}
            className={`relative px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
              isActive
                ? 'text-amber-300'
                : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            {isActive && (
              <motion.div
                layoutId="round-indicator"
                className="absolute inset-0 bg-amber-500/15 border border-amber-500/30 rounded-lg"
                transition={{ type: 'spring', stiffness: 350, damping: 28 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-1.5">
              {isCompleted && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />}
              {isCurrent && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />}
              Round {r}
            </span>
          </button>
        );
      })}
    </SpatialGlassPanel>
  );
}
