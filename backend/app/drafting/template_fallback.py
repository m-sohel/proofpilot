"""
Template Fallback — builds draft structure from facts without an LLM.

Produces the same DraftSentence[] structure as the LLM drafter,
ensuring the system works end-to-end when the LLM is disabled.
"""

from __future__ import annotations

from app.contracts import (
    Decision,
    DraftSentence,
    Fact,
    Recommendation,
    SentenceKind,
)


def build_template_draft(
    facts: list[Fact],
    decision: Decision,
) -> list[DraftSentence]:
    """
    Build a grounded draft response from facts using templates.
    No LLM required. Every claim sentence cites evidence.
    """
    sentences: list[DraftSentence] = []

    # Opening boilerplate
    sentences.append(DraftSentence(
        text="Thank you for bringing this dispute to our attention. We have reviewed the available evidence and present the following response.",
        evidence_ids=[],
        kind=SentenceKind.BOILERPLATE,
    ))

    # Group facts by type for organized presentation
    fact_groups: dict[str, list[Fact]] = {}
    for f in facts:
        fact_groups.setdefault(f.type.value, []).append(f)

    # Order record
    for f in fact_groups.get("order", []):
        amount = f.fields.get("amount", "")
        order_id = f.fields.get("order_id", "")
        addr = f.fields.get("address", "")
        parts = []
        if order_id:
            parts.append(f"Order {order_id}")
        if amount:
            parts.append(f"for ${amount}")
        if f.ts:
            parts.append(f"placed on {f.ts[:10]}")
        if addr:
            parts.append(f"with shipping address {addr}")
        if parts:
            sentences.append(DraftSentence(
                text=f"Our records show {' '.join(parts)}.",
                evidence_ids=[f.id],
                kind=SentenceKind.CLAIM,
            ))

    # Payment records
    for f in fact_groups.get("payment", []):
        txn_id = f.fields.get("transaction_id", "")
        amount = f.fields.get("amount", "")
        parts = []
        if txn_id:
            parts.append(f"Transaction {txn_id}")
        if amount:
            parts.append(f"of ${amount}")
        if f.ts:
            parts.append(f"was processed on {f.ts[:10]}")
        if parts:
            sentences.append(DraftSentence(
                text=" ".join(parts) + ".",
                evidence_ids=[f.id],
                kind=SentenceKind.CLAIM,
            ))

    # Courier events
    courier_facts = fact_groups.get("courier_event", [])
    dispatch = [f for f in courier_facts if f.fields.get("event") in ("dispatched", "package_dispatched")]
    delivery = [f for f in courier_facts if f.fields.get("event") == "delivered"]

    for f in dispatch:
        tracking = f.fields.get("tracking_id", "")
        text = "The package was dispatched"
        if tracking:
            text += f" with tracking number {tracking}"
        if f.ts:
            text += f" on {f.ts[:10]}"
        sentences.append(DraftSentence(
            text=text + ".",
            evidence_ids=[f.id],
            kind=SentenceKind.CLAIM,
        ))

    for f in delivery:
        addr = f.fields.get("address", "")
        text = "Delivery was confirmed"
        if addr:
            text += f" at {addr}"
        if f.ts:
            text += f" on {f.ts[:10]}"
        sentences.append(DraftSentence(
            text=text + ".",
            evidence_ids=[f.id],
            kind=SentenceKind.CLAIM,
        ))

    # Usage logs
    for f in fact_groups.get("usage_log", []):
        entry_count = f.fields.get("entry_count", 0)
        has_activity = f.fields.get("has_activity", False)
        if has_activity:
            sentences.append(DraftSentence(
                text=f"Service usage logs show {entry_count} recorded activities during the service period.",
                evidence_ids=[f.id],
                kind=SentenceKind.CLAIM,
            ))
        else:
            sentences.append(DraftSentence(
                text="Service usage logs show no recorded activity during the service period.",
                evidence_ids=[f.id],
                kind=SentenceKind.CLAIM,
            ))

    # Completion notices
    for f in fact_groups.get("completion_notice", []):
        text = "A service completion notice was issued"
        if f.ts:
            text += f" on {f.ts[:10]}"
        sentences.append(DraftSentence(
            text=text + ".",
            evidence_ids=[f.id],
            kind=SentenceKind.CLAIM,
        ))

    # Refund records
    for f in fact_groups.get("refund", []):
        refund_id = f.fields.get("refund_id", "")
        amount = f.fields.get("amount", "")
        text = "A refund"
        if refund_id:
            text += f" ({refund_id})"
        if amount:
            text += f" of ${amount}"
        text += " has been processed"
        if f.ts:
            text += f" on {f.ts[:10]}"
        sentences.append(DraftSentence(
            text=text + ".",
            evidence_ids=[f.id],
            kind=SentenceKind.CLAIM,
        ))

    # Decision-specific text
    if decision.recommendation == Recommendation.CHALLENGE:
        sentences.append(DraftSentence(
            text="Based on the evidence presented, we respectfully contest this dispute.",
            evidence_ids=[],
            kind=SentenceKind.BOILERPLATE,
        ))
    elif decision.recommendation == Recommendation.ACCEPT:
        sentences.append(DraftSentence(
            text="After reviewing the available evidence, we accept this dispute.",
            evidence_ids=[],
            kind=SentenceKind.BOILERPLATE,
        ))
    else:
        sentences.append(DraftSentence(
            text="This case requires additional review before a final response can be submitted.",
            evidence_ids=[],
            kind=SentenceKind.BOILERPLATE,
        ))

    # Closing boilerplate
    sentences.append(DraftSentence(
        text="We are committed to resolving this matter fairly and welcome any additional questions.",
        evidence_ids=[],
        kind=SentenceKind.BOILERPLATE,
    ))

    return sentences
