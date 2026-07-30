LLM Council — A Self-Grounding, Self-Doubting LLM Council

Most multi-model systems either pick one model's answer or blend several answers into one confident-sounding paragraph, regardless of whether the models actually agree. Council doesn't do that. Every claim made by the council earns or loses points based on real evidence. Confident, wrong claims are punished far harder than honest uncertainty. And when the council genuinely can't reach agreement, it says so — instead of faking a consensus.

The idea, in one sentence

Every agentic system today decides when to stop working the same dumb way: a hardcoded retry count. Ours decides it's done by tracking whether it's actually converging on the evidence — and it's honest when it isn't.

Architecture — 6 agents, 4 local + 2 cloud, zero billing
Question
   │
   ▼
Planner ──────────────────► decides how many rounds this question needs
   │
   ├────────────┬────────────┐
   ▼            ▼            (Member A and B run concurrently, not
Member A     Member B         one after another)
   │            │
   └─────┬──────┘
         ▼
   Fact Grounder ──► real web search per claim ──► verdict + points per claim
         ▼
   Disagreement Scorer ──► converge / retry / escalate
         │
    ┌────┴──────────────────────┐
    │                            │
 retry — members see each    escalate or converge
 other's scored claims,           │
 must defend/concede/rebut       ▼
 (max 3 rounds)               Chairman
    │                    (synthesize the answer, or honestly
    └──────► back to           present the unresolved
             Grounder            disagreement)
#	Agent	Model	Runs on
1	Planner	llama3.2:1b	Local (Ollama)
2	Council Member A	qwen2.5:1.5b	Local (Ollama)
3	Council Member B	gemma2:2b	Local (Ollama)
4	Fact Grounder	llama-3.1-8b-instant	Groq (free tier)
5	Disagreement Scorer	phi3.5:3.8b	Local (Ollama)
6	Chairman	llama-3.3-70b-versatile	Groq (free tier)

Any Groq call that fails or rate-limits automatically falls back to Gemini (gemini-2.5-flash, free tier). No paid API keys anywhere in this project.

What makes this different from a standard multi-model setup
Claims are checked, not just voted on. The Fact Grounder pulls specific factual claims out of each council member's answer and searches for real evidence (Wikipedia + DuckDuckGo Lite fallback) before anything gets scored.
Scoring is asymmetric, on purpose. Confidently wrong costs far more than honestly uncertain:
Outcome	Points
Confident claim, strongly supported	+2
Hedged claim, correct	+1
Honestly flagged as uncertain, genuinely unverifiable	0
Uncited claim, no source found either way	0
Hedged claim, wrong	-1
Confident claim, wrong	-3
Confident claim, wrong, repeated after being challenged	-5
Successful rebuttal of the other member's claim	+1 bonus
Disagreement is tracked as a trend, not a single check. The system watches whether disagreement is actually shrinking round over round. If it plateaus, more retries won't help — the system escalates instead of looping forever or forcing a fake answer.
Retry rounds are real counter-arguments. Each member is shown exactly what the other claimed and how it scored, and has to defend, concede, or rebut — not just answer the question again from scratch.
Nothing is cited that wasn't actually found. The Chairman is structurally restricted to citing only sources that appear in the real evidence trail — this was a bug we found and fixed during development (see below), and it's now enforced both by prompt and by a code-level guard.
Tech stack
Backend: FastAPI, WebSocket streaming for live agent status
Orchestration: 6-agent loop built on the original council.py structure
LLM providers: Groq (primary cloud) → Gemini (automatic fallback) + Ollama (local)
Search: Wikipedia API + DuckDuckGo Lite fallback
Frontend: React + TypeScript + Zustand + Framer Motion + Tailwind — a spatial,streaming agent answers, a live research trail (real queries, real results, as they happen), a claim-by-claim scoreboard, a disagreement trajectory chart, and a distinct visual state for "converged" vs. "escalated" answers\



