"""
Economics Engine — deterministic dispute recommendation.

Computes evidence_strength, p_win_estimate, net_ev, and recommendation.
The LLM NEVER chooses the recommendation; this is pure code.

Rules (priority order):
  1. Confirmed merchant error => accept
  2. Any high-severity contradiction => escalate
  3. net_ev > threshold AND evidence_strength > minimum => challenge
  4. net_ev <= 0 => accept (with economic rationale)
  5. Otherwise => escalate
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import get_config
from app.contracts import (
    Contradiction,
    Decision,
    Economics,
    Fact,
    Recommendation,
    Severity,
)
from app.pii import safe_log

logger = logging.getLogger(__name__)

_PLAYBOOKS_DIR = Path(__file__).resolve().parent / "playbooks"


def load_playbook(reason: str) -> dict[str, Any]:
    """Load the playbook for a dispute reason."""
    path = _PLAYBOOKS_DIR / f"{reason}.json"
    if not path.exists():
        logger.warning(safe_log(f"No playbook found for reason: {reason}"))
        return {"required_evidence": [], "known_failure_modes": [], "applicable_contradiction_rules": []}
    with open(path) as f:
        return json.load(f)


def compute_evidence_strength(
    facts: list[Fact],
    contradictions: list[Contradiction],
    playbook: dict[str, Any],
) -> float:
    """
    evidence_strength = sum of weights of present, non-contradicted required evidence
                        divided by total weight.
    """
    required = playbook.get("required_evidence", [])
    if not required:
        return 0.5  # no playbook — neutral

    # Get IDs of contradicted facts
    contradicted_ids: set[str] = set()
    for c in contradictions:
        contradicted_ids.update(c.fact_ids)

    # Check which required evidence types are present and non-contradicted
    total_weight = sum(r.get("weight", 0) for r in required)
    if total_weight == 0:
        return 0.5

    present_weight = 0.0
    for req in required:
        req_type = req.get("type", "")
        weight = req.get("weight", 0)

        # Find matching facts
        matching = [
            f for f in facts
            if f.type.value == req_type and f.id not in contradicted_ids
        ]
        if matching:
            # Use the highest-confidence match
            best_confidence = max(f.confidence for f in matching)
            present_weight += weight * best_confidence

    return round(present_weight / total_weight, 4)


def compute_p_win_estimate(
    evidence_strength: float,
    contradictions: list[Contradiction],
) -> float:
    """
    p_win_estimate = clamp(evidence_strength - contradiction penalties, 0.02, 0.95)
    """
    cfg = get_config()
    penalty = 0.0

    for c in contradictions:
        if c.severity == Severity.HIGH:
            penalty += cfg.contradiction_penalties.high
        elif c.severity == Severity.MEDIUM:
            penalty += cfg.contradiction_penalties.medium
        elif c.severity == Severity.LOW:
            penalty += cfg.contradiction_penalties.low

    raw = evidence_strength - penalty
    return round(max(0.02, min(0.95, raw)), 4)


def compute_net_ev(
    p_win: float,
    amount: float,
) -> Economics:
    """
    net_ev = p_win_estimate * amount - (handling_cost + dispute_fee)
    """
    cfg = get_config()
    expected_recovery = round(p_win * amount, 2)
    net_ev = round(expected_recovery - (cfg.economics.handling_cost + cfg.economics.dispute_fee), 2)

    return Economics(
        amount=amount,
        expected_recovery=expected_recovery,
        handling_cost=cfg.economics.handling_cost,
        dispute_fee=cfg.economics.dispute_fee,
        net_ev=net_ev,
    )


def find_missing_evidence(
    facts: list[Fact],
    playbook: dict[str, Any],
) -> list[str]:
    """Identify required evidence that is missing."""
    required = playbook.get("required_evidence", [])
    missing = []

    for req in required:
        req_type = req.get("type", "")
        desc = req.get("description", req_type)
        # Simple check: is there any fact of this type?
        matching = [f for f in facts if f.type.value == req_type]
        if not matching:
            missing.append(desc)

    return missing


def make_decision(
    facts: list[Fact],
    contradictions: list[Contradiction],
    amount: float,
    hours_left: float,
    reason: str,
    merchant_error: bool = False,
) -> Decision:
    """
    Deterministic decision engine. The LLM is NOT involved here.

    Priority rules:
      1. Confirmed merchant error => accept
      2. Any high-severity contradiction => escalate
      3. net_ev > threshold AND evidence_strength > minimum => challenge
      4. net_ev <= 0 => accept (economic rationale)
      5. Otherwise => escalate
    """
    cfg = get_config()
    playbook = load_playbook(reason)

    ev_strength = compute_evidence_strength(facts, contradictions, playbook)
    p_win = compute_p_win_estimate(ev_strength, contradictions)
    economics = compute_net_ev(p_win, amount)
    missing = find_missing_evidence(facts, playbook)

    reasons: list[str] = []
    recommendation: Recommendation

    # Rule 1: Confirmed merchant error
    if merchant_error:
        recommendation = Recommendation.ACCEPT
        reasons.append("Confirmed merchant error — accepting the dispute is the correct action.")
        if economics.net_ev > 0:
            reasons.append(f"Even though net expected value is ${economics.net_ev:.2f}, merchant error makes contesting inappropriate.")

    # Rule 2: Any high-severity contradiction
    elif any(c.severity == Severity.HIGH for c in contradictions):
        recommendation = Recommendation.ESCALATE
        high_contrs = [c for c in contradictions if c.severity == Severity.HIGH]
        reasons.append(f"Found {len(high_contrs)} high-severity contradiction(s) in the evidence:")
        for c in high_contrs:
            reasons.append(f"  • {c.explanation}")
        reasons.append("Manual review required before responding.")

    # Rule 3: Positive economics and sufficient evidence
    elif (economics.net_ev > cfg.economics.challenge_threshold
          and ev_strength > cfg.economics.min_evidence_strength):
        recommendation = Recommendation.CHALLENGE
        reasons.append(f"Net expected value: ${economics.net_ev:.2f} (above ${cfg.economics.challenge_threshold:.2f} threshold).")
        reasons.append(f"Evidence strength: {ev_strength:.0%} (above {cfg.economics.min_evidence_strength:.0%} minimum).")
        reasons.append(f"Estimated win probability: {p_win:.0%} (estimate, not a guarantee).")
        if missing:
            reasons.append(f"Note: {len(missing)} type(s) of evidence not found — gathering these would strengthen the case.")

    # Rule 4: Negative economics
    elif economics.net_ev <= 0:
        recommendation = Recommendation.ACCEPT
        reasons.append(f"Net expected value is ${economics.net_ev:.2f} — contesting would likely cost more than recovery.")
        reasons.append(f"Handling cost (${economics.handling_cost:.2f}) + dispute fee (${economics.dispute_fee:.2f}) exceed expected recovery (${economics.expected_recovery:.2f}).")
        reasons.append("Accepting the dispute is the economically rational choice.")

    # Rule 5: Default escalate
    else:
        recommendation = Recommendation.ESCALATE
        reasons.append(f"Evidence strength ({ev_strength:.0%}) or economics (net EV: ${economics.net_ev:.2f}) are borderline.")
        reasons.append("Recommend manual expert review before deciding.")
        if missing:
            reasons.append(f"Missing evidence types: {', '.join(missing)}")

    # Deadline warning
    deadline_warning = None
    if hours_left < cfg.economics.min_preparation_hours:
        deadline_warning = (
            f"⚠️ Only {hours_left:.1f} hours remain. Minimum preparation time is "
            f"{cfg.economics.min_preparation_hours:.0f} hours. Immediate action required."
        )

    decision = Decision(
        recommendation=recommendation,
        reasons=reasons,
        evidence_strength=ev_strength,
        p_win_estimate=p_win,
        economics=economics,
        missing_evidence=missing,
        hours_left=hours_left,
        requires_human_review=True,
        deadline_warning=deadline_warning,
    )

    logger.info(safe_log(
        f"Decision: {recommendation.value}",
        evidence_strength=f"{ev_strength:.2f}",
        p_win=f"{p_win:.2f}",
        net_ev=f"{economics.net_ev:.2f}",
    ))

    return decision
