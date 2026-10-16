"""
Unit tests for the Economics Engine.
"""

from app.contracts import Contradiction, Fact, FactType, Recommendation, Severity
from app.decision.economics import (
    compute_p_win_estimate,
    make_decision,
)


def test_merchant_error_always_accepts():
    # Even if amount is high and evidence is great
    facts = [
        Fact(id="F1", type=FactType.ORDER, text="Order confirmation", confidence=1.0, fields={}),
    ]
    decision = make_decision(
        facts=facts,
        contradictions=[],
        amount=500.0,
        hours_left=48.0,
        reason="product_not_received",
        merchant_error=True,
    )
    assert decision.recommendation == Recommendation.ACCEPT
    assert any("merchant error" in r.lower() for r in decision.reasons)


def test_high_severity_contradiction_escalates():
    facts = [
        Fact(id="F1", type=FactType.ORDER, text="Order record", confidence=1.0, fields={}),
        Fact(id="F2", type=FactType.COURIER_EVENT, text="Delivery event", confidence=1.0, fields={}),
    ]
    contradictions = [
        Contradiction(
            id="CONTR-1",
            rule_id="C1",
            severity=Severity.HIGH,
            fact_ids=["F1", "F2"],
            explanation="Delivery before dispatch",
        )
    ]
    decision = make_decision(
        facts=facts,
        contradictions=contradictions,
        amount=500.0,
        hours_left=48.0,
        reason="product_not_received",
    )
    assert decision.recommendation == Recommendation.ESCALATE
    assert any("high-severity contradiction" in r.lower() for r in decision.reasons)


def test_negative_net_ev_accepts():
    # Low amount dispute where fees ($15 + $15 = $30) exceed expected recovery
    facts = [
        Fact(id="F1", type=FactType.ORDER, text="Order record", confidence=1.0, fields={}),
        Fact(id="F2", type=FactType.COURIER_EVENT, text="Courier tracking", confidence=0.9, fields={"event": "delivered"}),
    ]
    # Amount $20: Even with 90% p_win, expected recovery is $18. Net EV = $18 - $30 = -$12.
    decision = make_decision(
        facts=facts,
        contradictions=[],
        amount=20.0,
        hours_left=48.0,
        reason="product_not_received",
    )
    assert decision.recommendation == Recommendation.ACCEPT
    assert decision.economics.net_ev <= 0
    assert any("economically rational" in r.lower() or "net expected value" in r.lower() for r in decision.reasons)


def test_positive_net_ev_and_strong_evidence_challenges():
    # Strong evidence for product_not_received (courier event + signature/delivery proof + order)
    facts = [
        Fact(id="F1", type=FactType.ORDER, text="Order confirmed", confidence=1.0, fields={}),
        Fact(id="F2", type=FactType.COURIER_EVENT, text="Courier tracking delivered with signature", confidence=1.0, fields={"event": "delivered"}),
        Fact(id="F3", type=FactType.POLICY_CLAUSE, text="Merchant terms of service", confidence=1.0, fields={}),
    ]
    decision = make_decision(
        facts=facts,
        contradictions=[],
        amount=350.0,
        hours_left=48.0,
        reason="product_not_received",
    )
    assert decision.recommendation == Recommendation.CHALLENGE
    assert decision.economics.net_ev > 10.0
    assert decision.evidence_strength >= 0.4


def test_borderline_evidence_escalates():
    # Positive net EV (300 * 0.2 = $60 recovery, net EV = $20), but evidence strength
    # is 0.20 (below 0.40 minimum threshold), so it falls through to ESCALATE.
    facts = [
        Fact(id="F1", type=FactType.ORDER, text="Order record", confidence=1.0, fields={}),
    ]
    decision = make_decision(
        facts=facts,
        contradictions=[],
        amount=300.0,
        hours_left=48.0,
        reason="product_not_received",
    )
    # Evidence strength is too low for auto-challenge, but economics are positive
    assert decision.recommendation == Recommendation.ESCALATE
    assert decision.economics.net_ev > 0
    assert decision.evidence_strength < 0.4


def test_deadline_warning():
    facts = [
        Fact(id="F1", type=FactType.ORDER, text="Order", confidence=1.0, fields={}),
    ]
    decision = make_decision(
        facts=facts,
        contradictions=[],
        amount=100.0,
        hours_left=2.0,  # Below 4h default threshold
        reason="product_not_received",
    )
    assert decision.deadline_warning is not None
    assert "Immediate action required" in decision.deadline_warning


def test_p_win_clamp():
    # Should not exceed 0.95 or fall below 0.02
    assert compute_p_win_estimate(1.5, []) == 0.95
    assert compute_p_win_estimate(-0.5, []) == 0.02
