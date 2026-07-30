"""The 6 distinct LLM agents for the LLM Council."""

import re
import math
import asyncio
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional

from .providers import call_agent, call_agent_json
from .web_search import search_web

# Core Incentive Prompt Rule (enforced across Council Members and Grounder)
CORE_INCENTIVE_RULE = (
    "CORE INCENTIVE RULE: Lying confidently is punished far harder than being honestly uncertain. "
    "A model should never bluff instead of hedging or admitting it doesn't know. "
    "Scoring Rubric: Confident correct = +2 | Hedged correct = +1 | Honest uncertain = 0 | Unverifiable = 0 | "
    "Hedged wrong = -1 | Confident wrong = -3 | Doubling down on wrong claim after challenge = -5 | Successful rebuttal bonus = +1."
)


# ---------------------------------------------------------------------------
# 1. PLANNER AGENT
# ---------------------------------------------------------------------------
async def run_planner(user_query: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Planner agent (powered by PLANNER_MODEL llama3.2:1b).
    Assesses question complexity and sets max_rounds (1 to 3).
    """
    planner_prompt = f"""You are the Planner Agent for an LLM Council.
Analyze the user's question and determine its complexity:
- Simple, straightforward factual questions (e.g. "What is the speed of light?") -> max_rounds: 1
- Moderately nuanced or analytical questions -> max_rounds: 2
- Contested, multi-faceted, or subjective/opinion questions -> max_rounds: 3

User Question: {user_query}

Output ONLY valid JSON in this exact structure:
{{
    "complexity": "simple" | "moderate" | "complex",
    "max_rounds": 1 | 2 | 3,
    "reasoning": "Brief explanation of why this complexity was chosen."
}}"""

    messages = [{"role": "user", "content": planner_prompt}]
    
    default_planner = lambda: {"complexity": "moderate", "max_rounds": 2, "reasoning": "Default moderate complexity."}
    
    parsed, raw_res = await call_agent_json("Planner", messages, default_factory=default_planner, request_id=request_id)
    
    # Sanitize max_rounds to 1..3
    max_rounds = parsed.get("max_rounds", 2)
    if not isinstance(max_rounds, int) or max_rounds < 1:
        max_rounds = 1
    elif max_rounds > 3:
        max_rounds = 3
    parsed["max_rounds"] = max_rounds
    
    return parsed


# ---------------------------------------------------------------------------
# 2. COUNCIL MEMBERS A & B AGENTS
# ---------------------------------------------------------------------------
async def run_council_members(
    user_query: str,
    round_number: int,
    previous_claims: List[Dict[str, Any]] = None,
    previous_answers: Dict[str, str] = None,
    request_id: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Run Council Member A (qwen2.5:1.5b) and Council Member B (gemma2:2b) concurrently.
    Member A: Persona 1 (Skeptical, risk-flagging, analytical).
    Member B: Persona 2 (Broader, opportunity-focused, creative).
    On retry rounds (round_number > 1), prompts include previous peer claims and Grounder verdicts.
    """
    previous_claims = previous_claims or []
    previous_answers = previous_answers or {}

    # System prompts with explicit Core Incentive Rule
    sys_a = (
        "You are Council Member A, a skeptical, risk-flagging, and highly analytical AI reasoning persona.\n"
        f"{CORE_INCENTIVE_RULE}"
    )
    sys_b = (
        "You are Council Member B, a broader, opportunity-focused, and creative AI reasoning persona.\n"
        f"{CORE_INCENTIVE_RULE}"
    )

    if round_number == 1:
        prompt_a = f"Provide your concise, thorough answer to the question:\n\nQuestion: {user_query}"
        prompt_b = f"Provide your concise, thorough answer to the question:\n\nQuestion: {user_query}"
    else:
        # Retry round: Include peer claims and Grounder verdicts
        claims_summary = "\n".join([
            f"- [{c.get('author')}] Claim: '{c.get('claim')}' | Verdict: {c.get('verdict')} | Points: {c.get('points')} | Reason: {c.get('reasoning')}"
            for c in previous_claims
        ])
        
        peer_a_ans = previous_answers.get("Council Member A", "")
        peer_b_ans = previous_answers.get("Council Member B", "")

        prompt_a = f"""This is Round {round_number} of the council debate on:
Question: {user_query}

Your previous answer: {peer_a_ans}
Council Member B's previous answer: {peer_b_ans}

Fact Grounder Claims & Verdicts from previous round:
{claims_summary}

INSTRUCTIONS FOR RETRY ROUND:
Review Council Member B's position and the Grounder's verdicts above.
Your next response MUST explicitly:
1. Defend your position with concrete reasoning/evidence, OR
2. Concede point(s) where Member B was verified correct, OR
3. Rebut Member B's specific claims.
WARNING: Do NOT repeat claims previously scored as wrong (-3 or -5) without new supporting evidence; repeating confidently-wrong claims incurs a harsh -5 double-down penalty!"""

        prompt_b = f"""This is Round {round_number} of the council debate on:
Question: {user_query}

Your previous answer: {peer_b_ans}
Council Member A's previous answer: {peer_a_ans}

Fact Grounder Claims & Verdicts from previous round:
{claims_summary}

INSTRUCTIONS FOR RETRY ROUND:
Review Council Member A's position and the Grounder's verdicts above.
Your next response MUST explicitly:
1. Defend your position with concrete reasoning/evidence, OR
2. Concede point(s) where Member A was verified correct, OR
3. Rebut Member A's specific claims.
WARNING: Do NOT repeat claims previously scored as wrong (-3 or -5) without new supporting evidence; repeating confidently-wrong claims incurs a harsh -5 double-down penalty!"""

    messages_a = [{"role": "system", "content": sys_a}, {"role": "user", "content": prompt_a}]
    messages_b = [{"role": "system", "content": sys_b}, {"role": "user", "content": prompt_b}]

    # Call Council Member A and B concurrently via asyncio.gather
    res_a, res_b = await asyncio.gather(
        call_agent("Council Member A", messages_a, request_id=request_id),
        call_agent("Council Member B", messages_b, request_id=request_id)
    )

    return res_a, res_b


# ---------------------------------------------------------------------------
# 3. FACT GROUNDER AGENT
# ---------------------------------------------------------------------------
async def run_fact_grounder(
    user_query: str,
    ans_a: str,
    ans_b: str,
    round_number: int,
    previous_claims: List[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Extracts checkable claims from Member A and B, runs web search, and applies exact scoring rubric:
      +2: Confident claim, strongly supported
      +1: Confident claim, partially supported
      +1: Hedged claim ("likely", "may be", "not fully certain but..."), correct
       0: Explicitly flagged uncertain by model, confirmed genuinely unverifiable (no penalty for honesty)
       0: Uncited / unverifiable claim, no source either way (never award positive on vagueness)
      -1: Hedged claim, wrong
      -3: Confident claim, wrong
      -5: Confident claim, wrong, AND member repeated/doubled down after challenge
      +1: Bonus if member's claim directly and correctly rebuts the other member's claim
    """
    previous_claims = previous_claims or []

    # Step 1: Extract claims via LLM
    extract_prompt = f"""You are the Fact Grounder Agent. Extract specific, checkable factual claims made by Council Member A and Council Member B.
{CORE_INCENTIVE_RULE}

Question: {user_query}

Council Member A Answer:
{ans_a}

Council Member B Answer:
{ans_b}

Extract 2 to 4 key checkable claims per member.
For each claim, indicate:
- "author": "Council Member A" or "Council Member B"
- "claim": exact claim text
- "confidence_level": "confident" | "hedged" | "explicitly_uncertain"
- "is_rebuttal": true if this claim is directly rebutting a claim made by the other member, else false

Output ONLY valid JSON array:
[
  {{
    "author": "Council Member A",
    "claim": "...",
    "confidence_level": "confident",
    "is_rebuttal": false
  }}
]"""

    messages = [{"role": "system", "content": f"You are the Fact Grounder Agent.\n{CORE_INCENTIVE_RULE}"}, {"role": "user", "content": extract_prompt}]
    default_claims = lambda: [
        {"author": "Council Member A", "claim": "General statement A", "confidence_level": "confident", "is_rebuttal": False},
        {"author": "Council Member B", "claim": "General statement B", "confidence_level": "confident", "is_rebuttal": False}
    ]

    claims_extracted, _ = await call_agent_json("Fact Grounder", messages, default_factory=default_claims, request_id=request_id)
    if not isinstance(claims_extracted, list):
        claims_extracted = default_claims()

    # Step 2: Web Search & Score each claim
    verdict_results = []
    
    for c in claims_extracted:
        author = c.get("author", "Unknown")
        claim_text = c.get("claim", "")
        conf_level = str(c.get("confidence_level", "confident")).lower()
        is_rebuttal = bool(c.get("is_rebuttal", False))
        
        if not claim_text or claim_text == "no_response":
            continue

        # Conduct web search
        search_snippets = await search_web(f"{user_query} {claim_text}", max_results=3)
        evidence_text = "\n".join([f"- {s['title']}: {s['snippet']} (URL: {s['url']})" for s in search_snippets]) if search_snippets else "No online sources found."

        # Evaluate claim against search evidence using LLM
        eval_prompt = f"""You are the Fact Grounder evaluating a claim against web evidence.
{CORE_INCENTIVE_RULE}

CRITICAL ABSENCE-OF-EVIDENCE RULE:
If you found ZERO sources for a claim (neither supporting nor contradicting), you MUST output support_status = unverifiable with 0 points. You are NEVER allowed to output support_status = wrong unless you can cite the specific contradicting source you found. No source found = unverifiable, always, no exceptions.

Claim: "{claim_text}"
Author: {author}
Confidence Level: {conf_level}
Is Rebuttal: {is_rebuttal}

Web Search Evidence:
{evidence_text}

Determine the grounding result:
- "support_status": "strongly_supported" | "partially_supported" | "unverifiable" | "wrong"
- "reasoning": "brief explanation based on evidence"

Output ONLY valid JSON:
{{
  "support_status": "strongly_supported" | "partially_supported" | "unverifiable" | "wrong",
  "reasoning": "..."
}}"""

        eval_messages = [{"role": "system", "content": f"You are the Fact Grounder.\n{CORE_INCENTIVE_RULE}"}, {"role": "user", "content": eval_prompt}]
        default_eval = lambda: {"support_status": "unverifiable", "reasoning": "No conclusive evidence found."}
        eval_res, _ = await call_agent_json("Fact Grounder", eval_messages, default_factory=default_eval, request_id=request_id)
        if isinstance(eval_res, list) and len(eval_res) > 0:
            eval_res = eval_res[0]
        if not isinstance(eval_res, dict):
            eval_res = default_eval()
        
        status = str(eval_res.get("support_status", "unverifiable")).lower()
        reasoning = eval_res.get("reasoning", "")

        # Check if member repeated/doubled down on a claim previously marked wrong
        doubled_down = False
        if round_number > 1 and previous_claims:
            for prev_c in previous_claims:
                if prev_c.get("author") == author and prev_c.get("points", 0) in [-3, -5, -1]:
                    prev_text = str(prev_c.get("claim", "")).lower()
                    curr_text = claim_text.lower()
                    if prev_text in curr_text or curr_text in prev_text or _compute_cosine_distance(prev_text, curr_text) < 0.5:
                        doubled_down = True
                        break

        # BUG 2 CODE GUARD: If no sources were found, verdict CANNOT be 'wrong' under any circumstances
        has_real_sources = bool(search_snippets) and evidence_text != "No online sources found."
        if (status == "wrong" or "wrong" in status) and not has_real_sources:
            logger.warning(
                f"[GROUNDER GUARD] Overriding invalid 'wrong' verdict to 'unverifiable' (0 pts) for claim '{claim_text[:50]}' "
                f"because zero contradicting sources were found."
            )
            status = "unverifiable"
            reasoning = "No online sources found to verify or contradict the claim. Marked as unverifiable (0 pts)."

        # Calculate exact points per PUNISHMENT & REWARD RUBRIC:
        points = 0
        verdict = status

        if status == "strongly_supported":
            if conf_level == "confident":
                points = 2
            elif conf_level == "hedged":
                points = 1
            else:
                points = 0
            
            if is_rebuttal:
                points += 1 # Rebuttal bonus
                verdict = "strongly_supported_rebuttal_bonus"

        elif status == "partially_supported":
            if conf_level in ["confident", "hedged"]:
                points = 1
            else:
                points = 0
            
            if is_rebuttal:
                points += 1 # Rebuttal bonus
                verdict = "partially_supported_rebuttal_bonus"

        elif status == "wrong":
            if conf_level == "hedged":
                points = -1
                verdict = "hedged_wrong"
            elif conf_level == "confident":
                if doubled_down:
                    points = -5
                    verdict = "wrong_doubled_down"
                else:
                    points = -3
                    verdict = "confident_wrong"
            else:
                points = -1
                verdict = "hedged_wrong"

        else: # unverifiable
            if conf_level == "explicitly_uncertain":
                points = 0 # No penalty for honesty
                verdict = "honest_uncertainty"
            else:
                points = 0 # Never award points for vagueness or missing source
                verdict = "unverifiable"

        verdict_results.append({
            "claim": claim_text,
            "author": author,
            "confidence_level": conf_level,
            "evidence": evidence_text[:400],
            "sources": search_snippets,
            "source_urls": [s.get("url", "") for s in search_snippets if s.get("url")],
            "verdict": verdict,
            "points": points,
            "reasoning": reasoning,
            "round": round_number
        })

    return verdict_results


# ---------------------------------------------------------------------------
# 4. DISAGREEMENT SCORER AGENT (SCORER_MODEL phi3.5:3.8b + Math Signals)
# ---------------------------------------------------------------------------
def _compute_cosine_distance(text1: str, text2: str) -> float:
    """Compute 1 - cosine_similarity between two texts using term frequencies."""
    def get_vec(text):
        words = re.findall(r'\w+', text.lower())
        return Counter(words)

    v1 = get_vec(text1)
    v2 = get_vec(text2)

    intersection = set(v1.keys()) & set(v2.keys())
    dot_product = sum(v1[x] * v2[x] for x in intersection)

    norm1 = math.sqrt(sum(v1[x]**2 for x in v1))
    norm2 = math.sqrt(sum(v2[x]**2 for x in v2))

    if norm1 == 0 or norm2 == 0:
        return 1.0

    similarity = dot_product / (norm1 * norm2)
    return max(0.0, min(1.0, 1.0 - similarity))


def calculate_disagreement_metrics(
    ans_a: str,
    ans_b: str,
    claim_verdicts: List[Dict[str, Any]],
    scores_a: int,
    scores_b: int,
    previous_disagreement: float = None,
    round_number: int = 1,
    max_rounds: int = 3
) -> Dict[str, Any]:
    if ans_a == "no_response" or ans_b == "no_response":
        return {
            "disagreement_score": 0.0,
            "contested_claim_count": 0,
            "source_support_ratio": 0.0,
            "semantic_divergence": 0.0,
            "trajectory_delta": 0.0,
            "score_gap": abs(scores_a - scores_b),
            "decision": "converge" if round_number >= max_rounds else "retry",
            "single_source": True,
            "reasoning": "Single source response available."
        }

    sem_div = _compute_cosine_distance(ans_a, ans_b)

    contested_count = sum(1 for c in claim_verdicts if "wrong" in str(c.get("verdict", "")) or c.get("points", 0) < 0)
    resolved_count = sum(1 for c in claim_verdicts if c.get("verdict") in ["strongly_supported", "partially_supported", "wrong"])
    total_claims = max(1, len(claim_verdicts))
    source_support_ratio = resolved_count / total_claims

    score_gap = abs(scores_a - scores_b)

    raw_score = (sem_div * 40.0) + (contested_count * 15.0) + (score_gap * 4.0) * (1.0 - 0.4 * source_support_ratio)
    disagreement_score = round(max(0.0, min(100.0, raw_score)), 2)

    if previous_disagreement is not None:
        trajectory_delta = round(disagreement_score - previous_disagreement, 2)
    else:
        trajectory_delta = 0.0

    if round_number >= max_rounds:
        decision = "escalate" if disagreement_score > 30.0 else "converge"
    elif disagreement_score < 25.0:
        decision = "converge"
    elif round_number > 1 and abs(trajectory_delta) <= 2.0 and disagreement_score > 40.0:
        decision = "escalate"
    else:
        decision = "retry"

    return {
        "disagreement_score": disagreement_score,
        "contested_claim_count": contested_count,
        "source_support_ratio": round(source_support_ratio, 2),
        "semantic_divergence": round(sem_div, 2),
        "trajectory_delta": trajectory_delta,
        "score_gap": score_gap,
        "decision": decision,
        "single_source": False,
        "reasoning": f"Calculated disagreement score is {disagreement_score} with decision '{decision}'."
    }


async def run_disagreement_scorer(
    ans_a: str,
    ans_b: str,
    claim_verdicts: List[Dict[str, Any]],
    scores_a: int,
    scores_b: int,
    previous_disagreement: Optional[float] = None,
    round_number: int = 1,
    max_rounds: int = 3,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Disagreement Scorer agent using SCORER_MODEL (phi3.5:3.8b).
    Combines deterministic mathematical signals with LLM reasoning.
    """
    metrics = calculate_disagreement_metrics(
        ans_a=ans_a,
        ans_b=ans_b,
        claim_verdicts=claim_verdicts,
        scores_a=scores_a,
        scores_b=scores_b,
        previous_disagreement=previous_disagreement,
        round_number=round_number,
        max_rounds=max_rounds
    )

    prompt = f"""You are the Disagreement Scorer Agent.
Analyze the disagreement level between Council Member A and B based on these metrics:

Metrics:
- Semantic Divergence: {metrics['semantic_divergence']}
- Contested Claims Count: {metrics['contested_claim_count']}
- Score Gap: {metrics['score_gap']}
- Score: {metrics['disagreement_score']}
- Suggested Decision: {metrics['decision']}

Answer A: {ans_a[:250]}
Answer B: {ans_b[:250]}

Output ONLY valid JSON:
{{
  "disagreement_score": {metrics['disagreement_score']},
  "decision": "{metrics['decision']}",
  "reasoning": "Brief explanation of disagreement state."
}}"""

    messages = [{"role": "user", "content": prompt}]
    default_scorer = lambda: {
        "disagreement_score": metrics["disagreement_score"],
        "decision": metrics["decision"],
        "reasoning": metrics["reasoning"]
    }

    parsed, _ = await call_agent_json("Disagreement Scorer", messages, default_factory=default_scorer, request_id=request_id)
    if isinstance(parsed, dict):
        if "disagreement_score" in parsed and isinstance(parsed["disagreement_score"], (int, float)):
            metrics["disagreement_score"] = round(float(parsed["disagreement_score"]), 2)
        if "decision" in parsed and parsed["decision"] in ["converge", "retry", "escalate"]:
            metrics["decision"] = str(parsed["decision"])
        if "reasoning" in parsed and parsed["reasoning"]:
            metrics["reasoning"] = str(parsed["reasoning"])

    return metrics


# ---------------------------------------------------------------------------
# 5. CHAIRMAN AGENT
# ---------------------------------------------------------------------------
async def run_chairman(
    user_query: str,
    decision: str,
    ans_a: str,
    ans_b: str,
    claim_verdicts: List[Dict[str, Any]],
    disagreement_summary: str = "",
    single_source: bool = False,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Chairman agent:
      If converged: Synthesizes final answer, citing verified claims.
      If escalated: Does NOT force blended answer. Clearly presents unresolved disagreements side-by-side.
    """
    verified_claims = [c for c in claim_verdicts if c.get("points", 0) > 0 or (c.get("sources") and len(c.get("sources")) > 0)]
    
    verified_text_lines = []
    for c in verified_claims:
        sources_str = ", ".join([f"{s.get('title')} ({s.get('url')})" for s in c.get("sources", []) if s.get("title")])
        if not sources_str and c.get("evidence") and c.get("evidence") != "No online sources found.":
            sources_str = c.get("evidence")[:120]
        if sources_str:
            verified_text_lines.append(f"- [{c['author']}] Claim: '{c['claim']}' | Verified Sources: {sources_str}")

    verified_text = "\n".join(verified_text_lines) if verified_text_lines else "NO EXTERNAL SOURCES FOUND."

    chairman_sys = (
        "You are the Chairman of the LLM Council.\n"
        f"{CORE_INCENTIVE_RULE}\n"
        "CRITICAL CITATION RULE: You may ONLY cite sources that appear verbatim in the 'Verified Ground-Truth Claims' list provided below. "
        "You MUST NEVER invent, hallucinate, or cite any source, organization, report, or institution (such as World Bank, Harvard, ILO, HBR, government departments) "
        "that does not explicitly appear in the input evidence. "
        "If 'Verified Ground-Truth Claims' says 'NO EXTERNAL SOURCES FOUND', you MUST state plainly that the council could not find external web sources for the specific claims made. "
        "Do NOT create a 'Verified Evidence' section or list fake citations in that case."
    )

    if decision == "converge":
        prompt = f"""Question: {user_query}

Council Member A Answer: {ans_a}
Council Member B Answer: {ans_b}

Verified Ground-Truth Claims:
{verified_text}

{"Note: Only a single council member responded. Synthesize based on available response without asserting false consensus." if single_source else ""}

Synthesize a single, comprehensive, highly accurate final answer strictly following the CRITICAL CITATION RULE above:"""

    else:  # escalate
        prompt = f"""Question: {user_query}

Council Member A Position: {ans_a}
Council Member B Position: {ans_b}

Claim Verification Summary:
{verified_text}

INSTRUCTIONS FOR ESCALATED RESPONSE:
Do NOT force a blended or fake consensus answer!
1. Present exact points of unresolved disagreement.
2. Present both positions honestly side-by-side.
Strictly adhere to the CRITICAL CITATION RULE: do not invent citations."""

    messages = [{"role": "system", "content": chairman_sys}, {"role": "user", "content": prompt}]
    res = await call_agent("Chairman", messages, request_id=request_id)
    
    raw_content = res.get("content", "")

    # BUG 1 CODE GUARD: Inspect and sanitize output if zero input sources existed
    has_input_sources = verified_text != "NO EXTERNAL SOURCES FOUND."
    if not has_input_sources:
        # Strip hallucinated 'Verified Evidence' / 'Sources Cited' sections
        lines = raw_content.splitlines()
        sanitized_lines = []
        in_fake_section = False
        
        for line in lines:
            lower = line.lower()
            if ("verified evidence" in lower or "sources cited:" in lower or "verified ground-truth" in lower) and not has_input_sources:
                in_fake_section = True
                logger.warning(f"[CHAIRMAN GUARD] Stripped fabricated citation header: '{line.strip()}'")
                continue
            
            if in_fake_section:
                if line.strip().startswith(("#", "1.", "2.", "3.", "4.", "-", "*")) and any(org in line for org in ["World Bank", "Harvard", "Department", "ILO", "IMF", "Bureau", "HBR", "Organisation"]):
                    logger.warning(f"[CHAIRMAN GUARD] Stripped fabricated citation line: '{line.strip()}'")
                    continue
                elif not line.strip():
                    in_fake_section = False
                    continue
            
            sanitized_lines.append(line)
            
        res["content"] = "\n".join(sanitized_lines).strip()

    return res

