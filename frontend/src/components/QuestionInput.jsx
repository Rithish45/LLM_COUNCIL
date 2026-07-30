import React, { useState } from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { Play, Sparkles, SlidersHorizontal } from 'lucide-react';
import { useCouncilStore } from '../store/councilStore';

export default function QuestionInput({ onSubmit }) {
  const [question, setQuestion] = useState('');
  const isRunning = useCouncilStore((state) => state.isRunning);
  const compareSingleModel = useCouncilStore((state) => state.compareSingleModel);
  const setCompareSingleModel = useCouncilStore((state) => state.setCompareSingleModel);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!question.trim() || isRunning) return;
    onSubmit(question.trim());
  };

  const presets = [
    "Should governments impose strict price controls on essential consumer food products during inflation?",
    "Should nuclear energy be classified as a primary green energy source for developing nations?",
    "Does artificial intelligence pose an existential risk to human decision-making autonomy?"
  ];

  return (
    <SpatialGlassPanel elevation="elevated" className="p-6 md:p-8 max-w-4xl mx-auto my-8">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-amber-400 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>LLM Council Query</span>
          </label>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-xs text-zinc-400 cursor-pointer hover:text-zinc-200 transition-colors">
              <input
                type="checkbox"
                checked={compareSingleModel}
                onChange={(e) => setCompareSingleModel(e.target.checked)}
                className="w-3.5 h-3.5 accent-amber-500 rounded bg-zinc-900 border-zinc-700"
              />
              <span>Compare against single-model answer</span>
            </label>
          </div>
        </div>

        <div className="relative flex items-center">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={isRunning}
            placeholder="Ask a contested, multi-faceted question..."
            className="w-full px-5 py-4 text-base rounded-xl spatial-glass-input pr-36 placeholder:text-zinc-500 font-medium"
          />
          <button
            type="submit"
            disabled={!question.trim() || isRunning}
            className="absolute right-2 px-5 py-2.5 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-950 font-semibold rounded-lg text-sm transition-all duration-200 shadow-[0_0_20px_rgba(245,158,11,0.25)] flex items-center gap-2"
          >
            {isRunning ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-zinc-950 border-t-transparent rounded-full animate-spin" />
                <span>Running...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Council</span>
              </>
            )}
          </button>
        </div>

        {/* Preset prompts */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-xs text-zinc-500 font-medium flex items-center gap-1">
            <SlidersHorizontal className="w-3 h-3" /> Sample Questions:
          </span>
          {presets.map((p, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setQuestion(p)}
              disabled={isRunning}
              className="text-xs px-2.5 py-1 rounded-md bg-zinc-900/60 hover:bg-zinc-800/80 border border-white/5 text-zinc-300 transition-colors text-left truncate max-w-xs"
            >
              {p}
            </button>
          ))}
        </div>
      </form>
    </SpatialGlassPanel>
  );
}
