"""
Unit tests for Grounding Verifier, including required adversarial cases.
"""

from app.contracts import DraftSentence, Fact, FactType, SentenceKind
from app.drafting.verifier import verify_draft


def _make_ground_truth_facts() -> list[Fact]:
    return [
        Fact(
            id="FACT-1",
            type=FactType.ORDER,
            text="Order ORD-1234 placed on 2026-03-01 for $149.99 by Alex Morgan.",
            ts="2026-03-01T10:00:00Z",
            fields={"order_id": "ORD-1234", "amount": 149.99, "date": "2026-03-01"},
        ),
        Fact(
            id="FACT-2",
            type=FactType.COURIER_EVENT,
            text="Package TRK-8888 delivered on 2026-03-04 to front porch.",
            ts="2026-03-04T15:00:00Z",
            fields={"tracking_id": "TRK-8888", "event": "delivered", "date": "2026-03-04"},
        ),
    ]


def test_valid_grounded_draft():
    facts = _make_ground_truth_facts()
    sentences = [
        DraftSentence(
            text="We have reviewed the dispute details carefully.",
            evidence_ids=[],
            kind=SentenceKind.BOILERPLATE,
        ),
        DraftSentence(
            text="Order ORD-1234 was placed on 2026-03-01 for $149.99.",
            evidence_ids=["FACT-1"],
            kind=SentenceKind.CLAIM,
        ),
        DraftSentence(
            text="Tracking record TRK-8888 confirms package was delivered on 2026-03-04.",
            evidence_ids=["FACT-2"],
            kind=SentenceKind.CLAIM,
        ),
    ]

    report = verify_draft(sentences, facts)
    assert len(report.kept) == 3
    assert len(report.removed) == 0
    assert len(report.todos) == 0


def test_adversarial_fabricated_date():
    # Cites FACT-2, but invents a delivery date "2026-12-31" not in the facts
    facts = _make_ground_truth_facts()
    sentences = [
        DraftSentence(
            text="The carrier confirmed delivery occurred on 2026-12-31.",
            evidence_ids=["FACT-2"],
            kind=SentenceKind.CLAIM,
        ),
    ]
    report = verify_draft(sentences, facts)
    assert len(report.kept) == 0
    assert len(report.removed) == 1
    assert "2026-12-31" in report.removed[0]["reason"]
    assert "Date" in report.removed[0]["reason"]


def test_adversarial_fabricated_tracking_number():
    # Cites FACT-2, but invents a tracking number "TRK-9999"
    facts = _make_ground_truth_facts()
    sentences = [
        DraftSentence(
            text="Delivery was confirmed under tracking TRK-9999 on 2026-03-04.",
            evidence_ids=["FACT-2"],
            kind=SentenceKind.CLAIM,
        ),
    ]
    report = verify_draft(sentences, facts)
    assert len(report.kept) == 0
    assert len(report.removed) == 1
    assert "TRK-9999" in report.removed[0]["reason"]
    assert "ID" in report.removed[0]["reason"]


def test_adversarial_fake_amount():
    # Cites FACT-1, but invents an amount "$599.99"
    facts = _make_ground_truth_facts()
    sentences = [
        DraftSentence(
            text="The customer purchased merchandise for $599.99 under ORD-1234.",
            evidence_ids=["FACT-1"],
            kind=SentenceKind.CLAIM,
        ),
    ]
    report = verify_draft(sentences, facts)
    assert len(report.kept) == 0
    assert len(report.removed) == 1
    assert "$599.99" in report.removed[0]["reason"]
    assert "Amount" in report.removed[0]["reason"]


def test_adversarial_nonexistent_evidence_id():
    # Cites an ID that does not exist in the fact set
    facts = _make_ground_truth_facts()
    sentences = [
        DraftSentence(
            text="Order ORD-1234 was confirmed.",
            evidence_ids=["FACT-NONEXISTENT-999"],
            kind=SentenceKind.CLAIM,
        ),
    ]
    report = verify_draft(sentences, facts)
    assert len(report.kept) == 0
    assert len(report.removed) == 1
    assert "nonexistent evidence ID" in report.removed[0]["reason"]


def test_rejection_of_absolute_promises():
    facts = _make_ground_truth_facts()
    sentences = [
        DraftSentence(
            text="We guarantee that the customer received the order on 2026-03-04.",
            evidence_ids=["FACT-2"],
            kind=SentenceKind.CLAIM,
        ),
        DraftSentence(
            text="The goods will definitely satisfy all requirements.",
            evidence_ids=["FACT-1"],
            kind=SentenceKind.CLAIM,
        ),
    ]
    report = verify_draft(sentences, facts)
    assert len(report.kept) == 0
    assert len(report.removed) == 2
    assert all("absolute promise" in r["reason"] for r in report.removed)


def test_rejection_of_uncited_claims():
    facts = _make_ground_truth_facts()
    sentences = [
        DraftSentence(
            text="The customer confirmed receipt via phone call.",
            evidence_ids=[],
            kind=SentenceKind.CLAIM,
        ),
    ]
    report = verify_draft(sentences, facts)
    assert len(report.kept) == 0
    assert len(report.removed) == 1
    assert "has no evidence IDs" in report.removed[0]["reason"]
