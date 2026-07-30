import { create } from 'zustand';

export const useCouncilStore = create((set, get) => ({
  // Run State
  isRunning: false,
  requestId: null,
  currentAgent: null,
  compareSingleModel: false,
  singleModelAnswer: null,

  // Council State
  roundNumber: 0,
  maxRounds: 1,
  activeRoundTab: 1,

  agentLogs: [],
  researchTrail: [],
  claimLedger: [],
  memberScores: { "Council Member A": 0, "Council Member B": 0 },
  confidenceTrajectory: [],
  decision: null,
  finalAnswer: "",
  memberAnswers: { "Council Member A": "", "Council Member B": "" },

  // Actions
  setCompareSingleModel: (val) => set({ compareSingleModel: val }),
  setActiveRoundTab: (tab) => set({ activeRoundTab: tab }),

  startRun: (requestId, question) => set({
    isRunning: true,
    requestId,
    currentAgent: 'Planner',
    roundNumber: 1,
    maxRounds: 2,
    activeRoundTab: 1,
    agentLogs: [],
    researchTrail: [],
    claimLedger: [],
    memberScores: { "Council Member A": 0, "Council Member B": 0 },
    confidenceTrajectory: [],
    decision: null,
    finalAnswer: "",
    memberAnswers: { "Council Member A": "", "Council Member B": "" },
    singleModelAnswer: get().compareSingleModel ? "Single-model generation running in parallel without council verification..." : null
  }),

  updateFromWebSocket: (msg) => {
    const state = get();
    
    if (msg.status === 'completed') {
      const finalState = msg.final_state || {};
      set({
        isRunning: false,
        currentAgent: null,
        roundNumber: finalState.round_number || state.roundNumber,
        maxRounds: finalState.max_rounds || state.maxRounds,
        memberScores: finalState.member_scores || state.memberScores,
        claimLedger: finalState.claim_verdicts || state.claimLedger,
        confidenceTrajectory: finalState.confidence_trajectory || state.confidenceTrajectory,
        decision: finalState.decision || state.decision,
        finalAnswer: finalState.final_answer || state.finalAnswer,
        memberAnswers: {
          "Council Member A": finalState.member_a_answer || state.memberAnswers["Council Member A"],
          "Council Member B": finalState.member_b_answer || state.memberAnswers["Council Member B"]
        }
      });
      return;
    }

    if (msg.agent) {
      set({ currentAgent: msg.status === 'running' ? msg.agent : null });

      // Append or update agent log
      set((prev) => {
        const existingIdx = prev.agentLogs.findIndex(l => l.agent === msg.agent && l.status === 'running');
        let newLogs = [...prev.agentLogs];
        if (existingIdx !== -1 && msg.status !== 'running') {
          newLogs[existingIdx] = msg;
        } else {
          newLogs.push(msg);
        }
        return { agentLogs: newLogs };
      });
    }

    // Live Research Trail updates
    if (msg.status === 'research_search' || msg.status === 'rate_limit_failover') {
      set((prev) => ({
        researchTrail: [...prev.researchTrail, {
          id: msg.id || Math.random().toString(36).substring(7),
          query: msg.query || msg.model || "Searching web evidence...",
          engine: msg.engine || (msg.provider ? `${msg.provider} (${msg.model})` : 'Wikipedia API'),
          status: msg.status === 'rate_limit_failover' ? 'failover' : 'success',
          results: msg.results || [],
          claimChecked: msg.claim || "",
          timestamp: msg.timestamp || Date.now()
        }]
      }));
    }
  },

  setFinalState: (finalState) => set({
    isRunning: false,
    currentAgent: null,
    roundNumber: finalState.round_number || 1,
    maxRounds: finalState.max_rounds || 2,
    memberScores: finalState.member_scores || { "Council Member A": 0, "Council Member B": 0 },
    claimLedger: finalState.claim_verdicts || [],
    confidenceTrajectory: finalState.confidence_trajectory || [],
    decision: finalState.decision || null,
    finalAnswer: finalState.final_answer || "",
    memberAnswers: {
      "Council Member A": finalState.member_a_answer || "",
      "Council Member B": finalState.member_b_answer || ""
    }
  })
}));
