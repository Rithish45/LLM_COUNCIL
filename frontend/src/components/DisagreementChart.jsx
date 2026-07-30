import React from 'react';
import SpatialGlassPanel from './SpatialGlassPanel';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { TrendingDown, Activity } from 'lucide-react';
import { useCouncilStore } from '../store/councilStore';

export default function DisagreementChart() {
  const confidenceTrajectory = useCouncilStore((state) => state.confidenceTrajectory);
  const decision = useCouncilStore((state) => state.decision);

  // Build chart data from trajectory
  const chartData = confidenceTrajectory.map((entry, idx) => ({
    round: `Round ${idx + 1}`,
    score: typeof entry === 'object' ? entry.disagreement_score : entry,
    delta: typeof entry === 'object' ? entry.trajectory_delta : 0
  }));

  // If no data yet, show placeholder
  if (chartData.length === 0) {
    return (
      <SpatialGlassPanel elevation="standard" className="p-6 my-6">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="p-2 rounded-lg bg-zinc-700/30 text-zinc-400 border border-zinc-600/20">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-100">Disagreement Trajectory</h3>
            <p className="text-xs text-zinc-400">Convergence vs escalation trend across debate rounds</p>
          </div>
        </div>
        <div className="text-center py-8 border border-dashed border-white/10 rounded-xl bg-zinc-900/30">
          <TrendingDown className="w-8 h-8 text-zinc-600 mx-auto mb-2 opacity-50" />
          <p className="text-xs text-zinc-400">Chart populates after at least one scored round completes...</p>
        </div>
      </SpatialGlassPanel>
    );
  }

  const latestScore = chartData[chartData.length - 1]?.score || 0;
  const trend = chartData.length > 1 ? (chartData[chartData.length - 1].score - chartData[0].score) : 0;

  return (
    <SpatialGlassPanel elevation="standard" className="p-6 my-6">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-zinc-700/30 text-zinc-400 border border-zinc-600/20">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-100">Disagreement Trajectory</h3>
            <p className="text-xs text-zinc-400">
              {decision === 'converge' ? 'Converged — trend resolved downward' :
               decision === 'escalate' ? 'Escalated — plateau detected, positions irreconcilable' :
               'Monitoring convergence trend...'}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className={`text-lg font-black font-mono ${latestScore > 40 ? 'text-rose-400' : latestScore > 20 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {latestScore.toFixed(1)}
          </span>
          <span className="text-[10px] text-zinc-400 block font-mono">
            {trend > 0 ? `↑ +${trend.toFixed(1)}` : trend < 0 ? `↓ ${trend.toFixed(1)}` : '→ 0.0'}
          </span>
        </div>
      </div>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -15, bottom: 0 }}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="round"
              tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: '#64748b', fontSize: 11, fontFamily: 'Inter' }}
              axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(14, 16, 22, 0.9)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '8px',
                backdropFilter: 'blur(12px)',
                fontSize: '12px',
                color: '#f8fafc',
                fontFamily: 'Inter'
              }}
              formatter={(value) => [`${value.toFixed(1)}`, 'Disagreement Score']}
            />
            <ReferenceLine y={25} stroke="rgba(16,185,129,0.3)" strokeDasharray="4 4" label={{ value: 'Converge', fill: '#64748b', fontSize: 10 }} />
            <ReferenceLine y={40} stroke="rgba(244,63,94,0.3)" strokeDasharray="4 4" label={{ value: 'Escalate', fill: '#64748b', fontSize: 10 }} />
            <Area
              type="monotone"
              dataKey="score"
              stroke="#f59e0b"
              strokeWidth={2}
              fill="url(#scoreGradient)"
              dot={{ fill: '#f59e0b', r: 4, strokeWidth: 2, stroke: '#0a0a0c' }}
              activeDot={{ r: 6, fill: '#f59e0b', strokeWidth: 2, stroke: '#fff' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </SpatialGlassPanel>
  );
}
