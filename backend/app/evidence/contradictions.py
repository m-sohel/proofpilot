"""
Contradiction Detection — deterministic rules for evidence inconsistencies.

Each rule is individually unit-tested. Rules:
  C1: delivery_before_dispatch (high)
  C2: address_mismatch between order and delivery (high)
  C3: refund_unlinked_to_transaction (medium)
  C4: completion_notice_before_service_end (medium)
  C5: duplicate_claim_without_second_settlement (high)
  C6: evidence_after_dispute_deadline (low)
"""

from __future__ import annotations

from datetime import datetime

from app.contracts import Contradiction, Fact, FactType, Severity


def detect_contradictions(
    facts: list[Fact],
    dispute_deadline: str | None = None,
) -> list[Contradiction]:
    """
    Run all contradiction rules against the fact set.

    Args:
        facts: List of extracted facts.
        dispute_deadline: ISO-8601 deadline for the dispute.

    Returns:
        List of detected contradictions.
    """
    contradictions: list[Contradiction] = []
    counter = 1

    for rule_fn in [
        _c1_delivery_before_dispatch,
        _c2_address_mismatch,
        _c3_refund_unlinked,
        _c4_completion_before_service_end,
        _c5_duplicate_without_settlement,
    ]:
        results = rule_fn(facts)
        for r in results:
            r.id = f"CONTR-{counter}"
            contradictions.append(r)
            counter += 1

    # C6 needs the deadline
    if dispute_deadline:
        results = _c6_evidence_after_deadline(facts, dispute_deadline)
        for r in results:
            r.id = f"CONTR-{counter}"
            contradictions.append(r)
            counter += 1

    return contradictions


# ── Individual Rules ──────────────────────────────────────────────────────────

def _c1_delivery_before_dispatch(facts: list[Fact]) -> list[Contradiction]:
    """C1: Delivery event timestamp is before dispatch timestamp (high severity)."""
    contradictions = []

    dispatch_facts = [f for f in facts if f.type == FactType.COURIER_EVENT
                      and f.fields.get("event") in ("dispatched", "package_dispatched")]
    delivery_facts = [f for f in facts if f.type == FactType.COURIER_EVENT
                      and f.fields.get("event") == "delivered"]

    for dispatch in dispatch_facts:
        for delivery in delivery_facts:
            # Match by tracking_id
            d_track = dispatch.fields.get("tracking_id", "")
            del_track = delivery.fields.get("tracking_id", "")
            if d_track and del_track and d_track == del_track:
                d_ts = _parse_ts(dispatch.ts)
                del_ts = _parse_ts(delivery.ts)
                if d_ts and del_ts and del_ts < d_ts:
                    contradictions.append(Contradiction(
                        id="",  # assigned by caller
                        rule_id="C1",
                        severity=Severity.HIGH,
                        fact_ids=[dispatch.id, delivery.id],
                        explanation=(
                            f"Delivery ({delivery.ts}) occurred before dispatch ({dispatch.ts}) "
                            f"for tracking {d_track}. This is physically impossible and suggests "
                            f"a data error or fabricated evidence."
                        ),
                    ))

    return contradictions


def _c2_address_mismatch(facts: list[Fact]) -> list[Contradiction]:
    """C2: Address mismatch between order shipping address and delivery location (high severity)."""
    contradictions = []

    order_facts = [f for f in facts if f.type == FactType.ORDER]
    delivery_facts = [f for f in facts if f.type == FactType.COURIER_EVENT
                      and f.fields.get("event") == "delivered"]

    for order in order_facts:
        order_addr = _normalize_address(order.fields.get("address", ""))
        if not order_addr:
            continue

        for delivery in delivery_facts:
            del_addr = _normalize_address(delivery.fields.get("address", ""))
            if not del_addr:
                continue

            if order_addr != del_addr:
                contradictions.append(Contradiction(
                    id="",
                    rule_id="C2",
                    severity=Severity.HIGH,
                    fact_ids=[order.id, delivery.id],
                    explanation=(
                        f"Order shipping address ({order.fields.get('address', '')}) does not match "
                        f"delivery location ({delivery.fields.get('address', '')}). "
                        f"Package may have been delivered to the wrong address."
                    ),
                ))

    return contradictions


def _c3_refund_unlinked(facts: list[Fact]) -> list[Contradiction]:
    """C3: Refund record not linked to any transaction (medium severity)."""
    contradictions = []

    refund_facts = [f for f in facts if f.type == FactType.REFUND]
    payment_txn_ids = {
        f.fields.get("transaction_id", "")
        for f in facts if f.type == FactType.PAYMENT
    }
    payment_txn_ids.discard("")

    for refund in refund_facts:
        refund_txn = refund.fields.get("transaction_id", "")
        if not refund_txn and not refund.fields.get("original_transaction_id", ""):
            # Refund has no transaction reference at all
            contradictions.append(Contradiction(
                id="",
                rule_id="C3",
                severity=Severity.MEDIUM,
                fact_ids=[refund.id],
                explanation=(
                    f"Refund {refund.fields.get('refund_id', 'unknown')} is not linked to "
                    f"any transaction. Cannot verify it relates to the disputed charge."
                ),
            ))
        elif refund_txn and refund_txn not in payment_txn_ids:
            # Refund references a transaction we don't have evidence for
            contradictions.append(Contradiction(
                id="",
                rule_id="C3",
                severity=Severity.MEDIUM,
                fact_ids=[refund.id],
                explanation=(
                    f"Refund references transaction {refund_txn} but no matching payment "
                    f"record was found in the evidence."
                ),
            ))

    return contradictions


def _c4_completion_before_service_end(facts: list[Fact]) -> list[Contradiction]:
    """C4: Completion notice timestamp is before the service period end (medium severity)."""
    contradictions = []

    completion_facts = [f for f in facts if f.type == FactType.COMPLETION_NOTICE]
    usage_facts = [f for f in facts if f.type == FactType.USAGE_LOG]

    for completion in completion_facts:
        comp_ts = _parse_ts(completion.ts) or _parse_ts(completion.fields.get("completion_date"))
        if not comp_ts:
            continue

        for usage in usage_facts:
            service_end = _parse_ts(usage.fields.get("service_end"))
            service_start = _parse_ts(usage.fields.get("service_start"))
            ref_ts = service_end or service_start
            if ref_ts and comp_ts < ref_ts:
                contradictions.append(Contradiction(
                    id="",
                    rule_id="C4",
                    severity=Severity.MEDIUM,
                    fact_ids=[completion.id, usage.id],
                    explanation=(
                        f"Service completion notice ({completion.ts}) was issued before "
                        f"service period completion ({usage.fields.get('service_end') or usage.fields.get('service_start', '')}). "
                        f"This suggests completion was premature or falsely reported."
                    ),
                ))

    return contradictions


def _c5_duplicate_without_settlement(facts: list[Fact]) -> list[Contradiction]:
    """C5: Duplicate charge claim but no evidence of second settlement (high severity)."""
    contradictions = []

    payment_facts = [f for f in facts if f.type == FactType.PAYMENT]

    if len(payment_facts) < 2:
        return contradictions

    # Check if any two payments share the same transaction ID
    txn_ids = [f.fields.get("transaction_id", "") for f in payment_facts]
    txn_ids = [t for t in txn_ids if t]

    seen: dict[str, list[Fact]] = {}
    for pf in payment_facts:
        txn = pf.fields.get("transaction_id", "")
        if txn:
            seen.setdefault(txn, []).append(pf)

    # If two payments have the same txn_id, it's a true duplicate
    for txn_id, pfs in seen.items():
        if len(pfs) >= 2:
            contradictions.append(Contradiction(
                id="",
                rule_id="C5",
                severity=Severity.HIGH,
                fact_ids=[pf.id for pf in pfs],
                explanation=(
                    f"Multiple payment records share transaction ID {txn_id}. "
                    f"This confirms a duplicate charge occurred. The merchant should "
                    f"accept the dispute unless one record is a settlement/refund."
                ),
            ))

    return contradictions


def _c6_evidence_after_deadline(facts: list[Fact], deadline: str) -> list[Contradiction]:
    """C6: Key evidence was created or recorded after the dispute deadline (low severity)."""
    contradictions = []

    deadline_ts = _parse_ts(deadline)
    if not deadline_ts:
        return contradictions

    evidence_types = {FactType.COURIER_EVENT, FactType.COMPLETION_NOTICE, FactType.REFUND}

    for fact in facts:
        if fact.type not in evidence_types:
            continue

        fact_ts = _parse_ts(fact.ts)
        if fact_ts and fact_ts > deadline_ts:
            contradictions.append(Contradiction(
                id="",
                rule_id="C6",
                severity=Severity.LOW,
                fact_ids=[fact.id],
                explanation=(
                    f"Evidence '{fact.text}' is dated {fact.ts}, which is after "
                    f"the dispute deadline ({deadline}). This evidence may not be "
                    f"admissible in the dispute process."
                ),
            ))

    return contradictions


# ── Helpers ──────────────────────────────────────────────────────────────────

def _parse_ts(ts_str: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp string."""
    if not ts_str:
        return None
    try:
        ts_str = str(ts_str).replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def _normalize_address(addr: str) -> str:
    """Normalize an address for comparison."""
    if not addr:
        return ""
    return " ".join(addr.lower().strip().split())
