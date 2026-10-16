"""
Unit tests for deterministic contradiction detection rules C1–C6.
"""

from app.contracts import Fact, FactType, Severity
from app.evidence.contradictions import (
    _c1_delivery_before_dispatch,
    _c2_address_mismatch,
    _c3_refund_unlinked,
    _c4_completion_before_service_end,
    _c5_duplicate_without_settlement,
    _c6_evidence_after_deadline,
    detect_contradictions,
)


def test_c1_delivery_before_dispatch():
    # Dispatch on 2026-03-05, Delivery on 2026-03-02 (Impossible!)
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.COURIER_EVENT,
            text="Package dispatched via FedEx",
            ts="2026-03-05T10:00:00Z",
            fields={"event": "dispatched", "tracking_id": "TRK-1234"},
        ),
        Fact(
            id="FACT-2",
            type=FactType.COURIER_EVENT,
            text="Package delivered to recipient",
            ts="2026-03-02T14:30:00Z",
            fields={"event": "delivered", "tracking_id": "TRK-1234"},
        ),
    ]
    results = _c1_delivery_before_dispatch(facts)
    assert len(results) == 1
    assert results[0].rule_id == "C1"
    assert results[0].severity == Severity.HIGH
    assert "Delivery" in results[0].explanation


def test_c1_valid_order_no_contradiction():
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.COURIER_EVENT,
            text="Package dispatched",
            ts="2026-03-02T10:00:00Z",
            fields={"event": "dispatched", "tracking_id": "TRK-1234"},
        ),
        Fact(
            id="FACT-2",
            type=FactType.COURIER_EVENT,
            text="Package delivered",
            ts="2026-03-05T14:30:00Z",
            fields={"event": "delivered", "tracking_id": "TRK-1234"},
        ),
    ]
    results = _c1_delivery_before_dispatch(facts)
    assert len(results) == 0


def test_c2_address_mismatch():
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.ORDER,
            text="Order shipping address: 123 Main St, Springfield",
            fields={"address": "123 Main St, Springfield"},
        ),
        Fact(
            id="FACT-2",
            type=FactType.COURIER_EVENT,
            text="Package delivered to 456 Elm Ave, Shelbyville",
            fields={"event": "delivered", "address": "456 Elm Ave, Shelbyville"},
        ),
    ]
    results = _c2_address_mismatch(facts)
    assert len(results) == 1
    assert results[0].rule_id == "C2"
    assert results[0].severity == Severity.HIGH
    assert "does not match" in results[0].explanation


def test_c2_matching_address():
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.ORDER,
            text="Order shipping address: 123 Main St, Springfield",
            fields={"address": "123 Main St, Springfield"},
        ),
        Fact(
            id="FACT-2",
            type=FactType.COURIER_EVENT,
            text="Package delivered to 123 Main St, Springfield",
            fields={"event": "delivered", "address": "123 Main St, Springfield "},
        ),
    ]
    results = _c2_address_mismatch(facts)
    assert len(results) == 0


def test_c3_refund_unlinked():
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.PAYMENT,
            text="Payment TXN-999 settled",
            fields={"transaction_id": "TXN-999"},
        ),
        Fact(
            id="FACT-2",
            type=FactType.REFUND,
            text="Refund processed for TXN-000",
            fields={"refund_id": "REF-1", "transaction_id": "TXN-000"},
        ),
    ]
    results = _c3_refund_unlinked(facts)
    assert len(results) == 1
    assert results[0].rule_id == "C3"
    assert results[0].severity == Severity.MEDIUM
    assert "no matching payment" in results[0].explanation


def test_c4_completion_before_service_end():
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.USAGE_LOG,
            text="Service period: 2026-04-01 to 2026-04-30",
            fields={"service_start": "2026-04-01T00:00:00Z", "service_end": "2026-04-30T23:59:59Z"},
        ),
        Fact(
            id="FACT-2",
            type=FactType.COMPLETION_NOTICE,
            text="Service completed notice",
            ts="2026-03-25T12:00:00Z",
            fields={"completion_date": "2026-03-25T12:00:00Z"},
        ),
    ]
    results = _c4_completion_before_service_end(facts)
    assert len(results) == 1
    assert results[0].rule_id == "C4"
    assert results[0].severity == Severity.MEDIUM


def test_c5_duplicate_without_settlement():
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.PAYMENT,
            text="Charge 1 for $120.00",
            fields={"transaction_id": "TXN-DUPE-1", "amount": 120.0},
        ),
        Fact(
            id="FACT-2",
            type=FactType.PAYMENT,
            text="Charge 2 for $120.00",
            fields={"transaction_id": "TXN-DUPE-1", "amount": 120.0},
        ),
    ]
    results = _c5_duplicate_without_settlement(facts)
    assert len(results) == 1
    assert results[0].rule_id == "C5"
    assert results[0].severity == Severity.HIGH
    assert "duplicate charge occurred" in results[0].explanation


def test_c6_evidence_after_deadline():
    deadline = "2026-05-01T00:00:00Z"
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.COURIER_EVENT,
            text="Package delivered late",
            ts="2026-05-05T12:00:00Z",
            fields={"event": "delivered"},
        ),
    ]
    results = _c6_evidence_after_deadline(facts, deadline)
    assert len(results) == 1
    assert results[0].rule_id == "C6"
    assert results[0].severity == Severity.LOW
    assert "after the dispute deadline" in results[0].explanation


def test_detect_contradictions_integration():
    facts = [
        Fact(
            id="FACT-1",
            type=FactType.COURIER_EVENT,
            text="Dispatched",
            ts="2026-03-05T10:00:00Z",
            fields={"event": "dispatched", "tracking_id": "TRK-1"},
        ),
        Fact(
            id="FACT-2",
            type=FactType.COURIER_EVENT,
            text="Delivered",
            ts="2026-03-02T10:00:00Z",
            fields={"event": "delivered", "tracking_id": "TRK-1"},
        ),
    ]
    contrs = detect_contradictions(facts)
    assert len(contrs) == 1
    assert contrs[0].id == "CONTR-1"
    assert contrs[0].rule_id == "C1"
