"""
Unit tests for Triage Queue ranking and scoring.
"""

from app.contracts import (
    CaseStatus,
    Decision,
    DisputeCase,
    DisputeReason,
    Economics,
    Recommendation,
)
from app.decision.triage import (
    compute_triage_score,
    compute_urgency,
    rank_queue,
)


def _make_dummy_case(
    case_id: str,
    amount: float,
    deadline: str,
    rec: Recommendation = Recommendation.CHALLENGE,
    net_ev: float = 100.0,
) -> DisputeCase:
    return DisputeCase(
        id=case_id,
        reason=DisputeReason.PRODUCT_NOT_RECEIVED,
        amount=amount,
        currency="USD",
        status=CaseStatus.NEW,
        created_at="2026-03-01T00:00:00Z",
        deadline=deadline,
        artifacts=[],
        decision=Decision(
            recommendation=rec,
            reasons=["Test reason"],
            evidence_strength=0.8,
            p_win_estimate=0.85,
            economics=Economics(
                amount=amount,
                expected_recovery=amount * 0.85,
                handling_cost=15.0,
                dispute_fee=15.0,
                net_ev=net_ev,
            ),
            hours_left=72.0,
        ),
    )


def test_urgency_tiers():
    assert compute_urgency(100.0) == 1.0  # > 72h
    assert compute_urgency(50.0) == 1.5   # 24-72h
    assert compute_urgency(10.0) == 2.0   # < 24h


def test_triage_score_formula():
    case = _make_dummy_case("C1", 200.0, "2099-01-01T00:00:00Z", net_ev=90.0)
    item = compute_triage_score(case, case.decision)
    # effort_hours = 1.0, urgency = 1.0 -> 90 / 1.0 * 1.0 = 90.0
    assert item.score == 90.0
    assert item.score_breakdown["effort_hours"] == 1.0


def test_overdue_pinned_to_top():
    # Overdue case
    overdue_case = _make_dummy_case("C-OLD", 50.0, "2020-01-01T00:00:00Z", net_ev=10.0)
    # High value future case
    future_case = _make_dummy_case("C-NEW", 1000.0, "2099-01-01T00:00:00Z", net_ev=800.0)

    queue = rank_queue([future_case, overdue_case])
    assert queue[0].case_id == "C-OLD"
    assert queue[0].is_overdue is True
    assert queue[0].score > 1_000_000


def test_escalate_ranked_by_amount_urgency():
    # Two escalate cases with different amounts
    c_esc1 = _make_dummy_case("E1", 100.0, "2099-01-01T00:00:00Z", rec=Recommendation.ESCALATE)
    c_esc2 = _make_dummy_case("E2", 500.0, "2099-01-01T00:00:00Z", rec=Recommendation.ESCALATE)

    item1 = compute_triage_score(c_esc1, c_esc1.decision)
    item2 = compute_triage_score(c_esc2, c_esc2.decision)

    assert item2.score > item1.score
    assert item2.score == 500.0 * 1.0
