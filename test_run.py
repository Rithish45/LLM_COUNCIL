import asyncio
import json
import logging
from backend.council import execute_council_run

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():
    question = "Should governments impose strict price controls on essential consumer food products during inflation?"
    print(f"\nStarting full council run for question: '{question}'\n")
    
    result = await execute_council_run(question)
    
    print("\n" + "="*80)
    print("FULL MULTI-ROUND COUNCIL RUN SUMMARY")
    print("="*80)
    print(f"Request ID:           {result.get('request_id')}")
    print(f"Total Rounds Run:     {result.get('round_number')} / {result.get('max_rounds')}")
    print(f"Final Decision:       {result.get('decision')}")
    print(f"Final Disagreement:   {result.get('disagreement_score')}")
    print(f"Accumulated Scores:   {result.get('member_scores')}")
    print("="*80)
    
    print("\n--- CLAIM VERDICTS & POINTS ASSIGNED ---")
    for i, c in enumerate(result.get('claim_verdicts', []), 1):
        print(f"[{i}] Round {c.get('round')} | Author: {c.get('author')}")
        print(f"    Claim: '{c.get('claim')}'")
        print(f"    Verdict: {c.get('verdict')} | Points: {c.get('points')} | Confidence: {c.get('confidence_level')}")
        print(f"    Reasoning: {c.get('reasoning')}")
        print("-" * 60)
        
    print("\n--- ANSWER HISTORY ACROSS ROUNDS ---")
    for ans in result.get('answer_history', []):
        print(f"\n[Round {ans.get('round')}]")
        print(f"  Council Member A: {ans.get('Council Member A')[:250]}...")
        print(f"  Council Member B: {ans.get('Council Member B')[:250]}...")
        
    print("\n" + "="*80)
    print("FINAL CHAIRMAN ANSWER")
    print("="*80)
    print(result.get('final_answer'))

if __name__ == "__main__":
    asyncio.run(main())
