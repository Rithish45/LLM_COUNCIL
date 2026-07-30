"""State object management and multi-round 6-agent council orchestration flow."""

import uuid
import time
import logging
from typing import List, Dict, Any, Tuple, Optional

from .agents import (
    run_planner,
    run_council_members,
    run_fact_grounder,
    run_disagreement_scorer,
    run_chairman
)
from .providers import register_status_callback, unregister_status_callback

logger = logging.getLogger("llm_council.orchestration")

# In-memory storage for active/completed council state runs
_COUNCIL_RUNS: Dict[str, Dict[str, Any]] = {}

def get_council_state(request_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve full state object by request_id."""
    return _COUNCIL_RUNS.get(request_id)


async def execute_council_run(question: str, request_id: str = None) -> Dict[str, Any]:
    """
    Executes the full 6-agent multi-round council flow.
    Tracks state object across rounds.
    """
    if not request_id:
        request_id = str(uuid.uuid4())

    state = {
        "request_id": request_id,
        "question": question,
        "round_number": 0,
        "max_rounds": 1,
        "member_a_answer": "",
        "member_b_answer": "",
        "answer_history": [],
        "claim_verdicts": [],
        "member_scores": {
            "Council Member A": 0,
            "Council Member B": 0
        },
        "disagreement_score": 0.0,
        "confidence_trajectory": [],
        "decision": "pending",
        "final_answer": "",
        "disagreement_summary": "",
        "agent_status_log": [],
        "errors": []
    }

    _COUNCIL_RUNS[request_id] = state

    def handle_log(log_entry: Dict[str, Any]):
        if log_entry.get("request_id") == request_id or log_entry.get("request_id") is None:
            state["agent_status_log"].append(log_entry)

    register_status_callback(handle_log)

    try:
        # STEP 1: Planner Agent
        planner_res = await run_planner(question, request_id=request_id)
        max_rounds = planner_res.get("max_rounds", 2)
        state["max_rounds"] = max_rounds
        logger.info(f"[{request_id}] Planner assigned max_rounds={max_rounds}")

        prev_disagreement = None
        current_round = 1

        while current_round <= max_rounds:
            state["round_number"] = current_round
            logger.info(f"[{request_id}] Starting Round {current_round}/{max_rounds}")

            # STEP 2: Council Members A & B (Concurrent)
            prev_answers = {
                "Council Member A": state["member_a_answer"],
                "Council Member B": state["member_b_answer"]
            }
            
            res_a, res_b = await run_council_members(
                user_query=question,
                round_number=current_round,
                previous_claims=state["claim_verdicts"],
                previous_answers=prev_answers,
                request_id=request_id
            )

            ans_a = res_a.get("content", "no_response")
            ans_b = res_b.get("content", "no_response")

            state["member_a_answer"] = ans_a
            state["member_b_answer"] = ans_b
            state["answer_history"].append({
                "round": current_round,
                "Council Member A": ans_a,
                "Council Member B": ans_b
            })

            # Check if both members failed
            if ans_a == "no_response" and ans_b == "no_response":
                state["errors"].append(f"Round {current_round}: Both council members failed to respond.")
                state["decision"] = "escalate"
                break

            # STEP 3: Fact Grounder Agent
            round_claims = await run_fact_grounder(
                user_query=question,
                ans_a=ans_a,
                ans_b=ans_b,
                round_number=current_round,
                previous_claims=state["claim_verdicts"],
                request_id=request_id
            )

            state["claim_verdicts"].extend(round_claims)

            # Update running scores
            for c in round_claims:
                auth = c.get("author")
                if auth in state["member_scores"]:
                    state["member_scores"][auth] += c.get("points", 0)

            # STEP 4: Disagreement Scorer Agent
            metrics = await run_disagreement_scorer(
                ans_a=ans_a,
                ans_b=ans_b,
                claim_verdicts=round_claims,
                scores_a=state["member_scores"]["Council Member A"],
                scores_b=state["member_scores"]["Council Member B"],
                previous_disagreement=prev_disagreement,
                round_number=current_round,
                max_rounds=max_rounds,
                request_id=request_id
            )

            disagreement_score = metrics["disagreement_score"]
            decision = metrics["decision"]
            
            state["disagreement_score"] = disagreement_score
            state["confidence_trajectory"].append(disagreement_score)
            state["decision"] = decision
            prev_disagreement = disagreement_score

            logger.info(f"[{request_id}] Round {current_round} Score={disagreement_score}, Decision={decision}")

            if decision in ["converge", "escalate"] or current_round >= max_rounds:
                break

            current_round += 1

        # STEP 5: Chairman Agent
        chairman_res = await run_chairman(
            user_query=question,
            decision=state["decision"],
            ans_a=state["member_a_answer"],
            ans_b=state["member_b_answer"],
            claim_verdicts=state["claim_verdicts"],
            disagreement_summary=f"Disagreement score ended at {state['disagreement_score']}",
            single_source=(state["member_a_answer"] == "no_response" or state["member_b_answer"] == "no_response"),
            request_id=request_id
        )

        state["final_answer"] = chairman_res.get("content", "")
        if state["decision"] == "escalate":
            state["disagreement_summary"] = f"Unresolved disagreement (score: {state['disagreement_score']}). Both member positions were preserved."

    except Exception as e:
        logger.error(f"Error executing council run {request_id}: {e}", exc_info=True)
        state["errors"].append(str(e))
        state["decision"] = "error"
        state["final_answer"] = f"An unexpected error occurred: {e}"
    finally:
        unregister_status_callback(handle_log)

    return state
