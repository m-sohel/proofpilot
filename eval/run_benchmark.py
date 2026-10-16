"""
ProofPilot Benchmark Runner.

Evaluates:
1. Extraction accuracy against labelled facts
2. Contradiction detection precision and recall
3. Grounding rate & hallucinated count
4. Net financial return vs 'Contest All' and 'Concede All' baselines

Usage:
    python eval/run_benchmark.py [--all] [--provider mock|ollama]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add backend and root to sys.path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_ROOT))

from app.contracts import CaseArtifact, CaseStatus, DisputeCase, DisputeReason
from app.decision.economics import make_decision
from app.decision.triage import compute_hours_left
from app.drafting.drafter import draft_response
from app.drafting.template_fallback import build_template_draft
from app.drafting.verifier import verify_draft
from app.evidence.contradictions import detect_contradictions
from app.extraction.extractor import extract_facts
from app.llm.mock_client import MockLLMClient
from app.llm.ollama_client import OllamaClient

from eval.metrics import aggregate_benchmark, evaluate_case_performance


async def run_benchmark(use_all_cases: bool = False, provider: str = "mock") -> dict:
    cases_dir = _ROOT / "data" / "cases"
    labels_dir = _ROOT / "data" / "labels"
    split_file = _ROOT / "data" / "split.json"

    with open(split_file) as f:
        split_data = json.load(f)

    case_ids = split_data.get("train_ids", []) + split_data.get("test_ids", []) if use_all_cases else split_data.get("test_ids", [])

    print("\n=======================================================")
    print(f"  ProofPilot Benchmark Suite — Evaluating {len(case_ids)} Cases")
    print(f"  Mode: {'Full Dataset' if use_all_cases else 'Holdout Test Split (20%)'}")
    print(f"  LLM Provider: {provider}")
    print("=======================================================\n")

    if provider == "ollama":
        llm_client = OllamaClient()
    else:
        llm_client = MockLLMClient()

    results = []

    for idx, case_id in enumerate(case_ids):
        case_path = cases_dir / f"{case_id}.json"
        label_path = labels_dir / f"{case_id}.json"

        if not case_path.exists() or not label_path.exists():
            continue

        with open(case_path) as cf:
            raw_case = json.load(cf)
        with open(label_path) as lf:
            label = json.load(lf)

        case = DisputeCase(
            id=raw_case["id"],
            reason=DisputeReason(raw_case["reason"]),
            amount=raw_case["amount"],
            currency=raw_case.get("currency", "USD"),
            status=CaseStatus.NEW,
            created_at=raw_case.get("created_at", "2026-03-01T00:00:00Z"),
            deadline=raw_case.get("deadline", "2026-04-01T00:00:00Z"),
            merchant_name=raw_case.get("merchant_name", "Merchant"),
            customer_id=raw_case.get("customer_id", ""),
            merchant_error=raw_case.get("merchant_error", False),
            artifacts=[CaseArtifact(**a) for a in raw_case.get("artifacts", [])],
        )

        # 1. Extraction
        facts = await extract_facts(case.artifacts, llm_client, case_id=case.id)
        case.facts = facts

        # 2. Contradictions
        contradictions = detect_contradictions(facts, case.deadline)
        case.contradictions = contradictions

        # 3. Decision Economics
        hours_left = compute_hours_left(case.deadline)
        decision = make_decision(
            facts=facts,
            contradictions=contradictions,
            amount=case.amount,
            hours_left=hours_left,
            reason=case.reason.value,
            merchant_error=case.merchant_error,
        )
        case.decision = decision

        # 4. Draft & Verify
        if provider == "mock":
            raw_draft = build_template_draft(facts, decision)
        else:
            raw_draft = await draft_response(facts, decision, llm_client)

        report = verify_draft(raw_draft, facts)
        case.draft = report.kept
        case.grounding_report = report

        # 5. Evaluate
        perf = evaluate_case_performance(case, label, case_index=idx)
        results.append(perf)
        print(f"[{idx+1:02d}/{len(case_ids):02d}] {case.id} ({case.reason.value[:18]}): Rec={perf['recommendation']:<9} Exp={perf['expected_recommendation']:<9} Win={str(perf['simulated_win']):<5} ExtAcc={perf['extraction_accuracy']:.2f}")

    benchmark = aggregate_benchmark(results)

    print("\n" + "=" * 60)
    print("                 BENCHMARK RESULTS REPORT")
    print("=" * 60)
    print(f"Total Cases Evaluated:       {benchmark.total_cases}")
    print(f"Extraction Accuracy:         {benchmark.extraction_accuracy * 100:.1f}%")
    print(f"Contradiction Precision:     {benchmark.contradiction_precision * 100:.1f}%")
    print(f"Contradiction Recall:        {benchmark.contradiction_recall * 100:.1f}%")
    print(f"Grounding Rate:              {benchmark.grounding_rate * 100:.1f}%")
    print(f"Hallucinated Entities:       {benchmark.hallucinated_count} (Target: 0)")
    print("-" * 60)
    print(f"ProofPilot Net Return:       ${benchmark.proofpilot_net_return:>10.2f}")
    print(f"Baseline: Contest All:       ${benchmark.contest_all_net_return:>10.2f}")
    print(f"Baseline: Concede All:       ${benchmark.concede_all_net_return:>10.2f}")
    print(f"Value Added vs Contest All:  +${(benchmark.proofpilot_net_return - benchmark.contest_all_net_return):>9.2f}")
    print(f"Value Added vs Concede All:  +${(benchmark.proofpilot_net_return - benchmark.concede_all_net_return):>9.2f}")
    print("=" * 60 + "\n")

    return {
        "total_cases": benchmark.total_cases,
        "extraction_accuracy": benchmark.extraction_accuracy,
        "contradiction_precision": benchmark.contradiction_precision,
        "contradiction_recall": benchmark.contradiction_recall,
        "grounding_rate": benchmark.grounding_rate,
        "hallucinated_count": benchmark.hallucinated_count,
        "proofpilot_net_return": benchmark.proofpilot_net_return,
        "contest_all_net_return": benchmark.contest_all_net_return,
        "concede_all_net_return": benchmark.concede_all_net_return,
        "case_summaries": benchmark.case_summaries,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ProofPilot Benchmark")
    parser.add_argument("--all", action="store_true", help="Evaluate all 50 cases instead of only test split")
    parser.add_argument("--provider", default="mock", choices=["mock", "ollama"], help="LLM provider")
    args = parser.parse_args()

    asyncio.run(run_benchmark(use_all_cases=args.all, provider=args.provider))
