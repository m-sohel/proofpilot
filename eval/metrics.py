"""
Evaluation metrics and outcome simulation for ProofPilot.

NOTE: All results come from synthetic data and a simulated outcome model,
and are not evidence of real-world performance.
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure backend directory is in sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.config import get_config
from app.contracts import Contradiction, DisputeCase, Recommendation, Severity
from app.drafting.verifier import verify_draft


@dataclass
class BenchmarkMetrics:
    total_cases: int = 0
    extraction_accuracy: float = 0.0
    contradiction_precision: float = 0.0
    contradiction_recall: float = 0.0
    grounding_rate: float = 0.0
    hallucinated_count: int = 0
    proofpilot_net_return: float = 0.0
    contest_all_net_return: float = 0.0
    concede_all_net_return: float = 0.0
    case_summaries: list[dict[str, Any]] = field(default_factory=list)


def simulate_case_win(
    evidence_strength: float,
    contradictions: list[Contradiction],
    case_seed: int,
) -> bool:
    """
    Transparent, documented simulation of issuer chargeback outcome:
    - Base win likelihood = evidence_strength
    - Penalties: high severity (-0.40 each), medium (-0.15 each), low (-0.05 each)
    - Pseudo-random noise seeded per case in range [-0.05, 0.05]
    - Outcome is WIN if win_likelihood >= 0.50
    """
    penalty = sum(
        0.40 if c.severity == Severity.HIGH
        else 0.15 if c.severity == Severity.MEDIUM
        else 0.05
        for c in contradictions
    )
    rng = random.Random(case_seed)
    noise = rng.uniform(-0.05, 0.05)
    win_likelihood = max(0.0, min(1.0, evidence_strength - penalty + noise))
    return win_likelihood >= 0.50


def evaluate_case_performance(
    case: DisputeCase,
    label: dict[str, Any],
    case_index: int = 0,
) -> dict[str, Any]:
    """Evaluate a single analyzed and drafted case against ground-truth labels."""
    cfg = get_config()
    handling_cost = cfg.economics.handling_cost
    dispute_fee = cfg.economics.dispute_fee
    total_fee = handling_cost + dispute_fee

    # 1. Extraction accuracy: check if expected fact types were found
    expected_facts = label.get("expected_facts", [])
    extracted_types = {f.type.value for f in case.facts}
    if expected_facts:
        matched = sum(1 for ef in expected_facts if ef.get("type") in extracted_types)
        extraction_acc = matched / len(expected_facts)
    else:
        extraction_acc = 1.0

    # 2. Contradiction precision & recall
    seeded_rule_ids = set(label.get("seeded_contradiction_ids", []))
    detected_rule_ids = {c.rule_id for c in case.contradictions}

    tp = len(seeded_rule_ids & detected_rule_ids)
    fp = len(detected_rule_ids - seeded_rule_ids)
    fn = len(seeded_rule_ids - detected_rule_ids)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    # 3. Grounding & Hallucinations
    report = case.grounding_report or verify_draft(case.draft, case.facts)
    total_draft_sentences = len(report.kept) + len(report.removed)
    grounding_rate = len(report.kept) / total_draft_sentences if total_draft_sentences > 0 else 1.0
    hallucination_count = len(report.removed)

    # 4. Financial simulation
    ev_strength = case.decision.evidence_strength if case.decision else 0.5
    won = simulate_case_win(ev_strength, case.contradictions, case_seed=case_index + 1000)

    # Outcome if contested
    contested_pnl = (case.amount - total_fee) if won else -total_fee
    # Outcome if conceded
    conceded_pnl = 0.0

    # ProofPilot decision
    rec = case.decision.recommendation if case.decision else Recommendation.ACCEPT
    if rec == Recommendation.CHALLENGE:
        proofpilot_pnl = contested_pnl
    else:
        proofpilot_pnl = conceded_pnl

    return {
        "case_id": case.id,
        "amount": case.amount,
        "recommendation": rec.value if isinstance(rec, Recommendation) else str(rec),
        "expected_recommendation": label.get("expected_recommendation"),
        "simulated_win": won,
        "extraction_accuracy": round(extraction_acc, 3),
        "contradiction_precision": round(precision, 3),
        "contradiction_recall": round(recall, 3),
        "grounding_rate": round(grounding_rate, 3),
        "hallucination_count": hallucination_count,
        "proofpilot_pnl": round(proofpilot_pnl, 2),
        "contest_all_pnl": round(contested_pnl, 2),
        "concede_all_pnl": round(conceded_pnl, 2),
    }


def aggregate_benchmark(results: list[dict[str, Any]]) -> BenchmarkMetrics:
    """Aggregate per-case evaluation results into overall benchmark metrics."""
    if not results:
        return BenchmarkMetrics()

    n = len(results)
    avg_ext = sum(r["extraction_accuracy"] for r in results) / n
    avg_prec = sum(r["contradiction_precision"] for r in results) / n
    avg_rec = sum(r["contradiction_recall"] for r in results) / n
    avg_ground = sum(r["grounding_rate"] for r in results) / n
    total_hallucinations = sum(r["hallucination_count"] for r in results)

    pp_total = sum(r["proofpilot_pnl"] for r in results)
    contest_total = sum(r["contest_all_pnl"] for r in results)
    concede_total = sum(r["concede_all_pnl"] for r in results)

    return BenchmarkMetrics(
        total_cases=n,
        extraction_accuracy=round(avg_ext, 4),
        contradiction_precision=round(avg_prec, 4),
        contradiction_recall=round(avg_rec, 4),
        grounding_rate=round(avg_ground, 4),
        hallucinated_count=total_hallucinations,
        proofpilot_net_return=round(pp_total, 2),
        contest_all_net_return=round(contest_total, 2),
        concede_all_net_return=round(concede_total, 2),
        case_summaries=results,
    )
