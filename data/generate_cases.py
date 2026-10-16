"""
Synthetic case generator for ProofPilot.

Generates ~50 seeded, reproducible dispute cases with messy artifacts
(courier logs, chat transcripts, order/payment records, policy, usage logs, refunds).
Seeds known contradictions on a defined share of cases.
Writes ground-truth labels per case.
Holds out 20% as a test split.

ALL DATA IS SYNTHETIC. No real customer or payment data.
"""

from __future__ import annotations

import json
import os
import random
import string
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────────────

SEED = 42
NUM_CASES = 50
TEST_SPLIT_RATIO = 0.20
CONTRADICTION_RATE = 0.35  # 35% of cases get seeded contradictions

REASONS = ["product_not_received", "duplicate_charge", "service_not_provided"]
REASON_WEIGHTS = [0.40, 0.30, 0.30]

MERCHANT_NAMES = [
    "TechHaven Electronics", "GreenLeaf Organics", "UrbanStyle Clothing",
    "SwiftFix Repairs", "CloudStream Media", "FitGear Sports",
    "PureGlow Cosmetics", "DataVault Services", "AquaPure Filters",
    "NovaByte Software",
]

FIRST_NAMES = [
    "Alex", "Jordan", "Morgan", "Casey", "Riley", "Quinn", "Avery",
    "Blake", "Drew", "Sage", "River", "Sky", "Phoenix", "Harper", "Emerson",
]

LAST_NAMES = [
    "Smith", "Chen", "Kumar", "Garcia", "Williams", "Brown", "Jones",
    "Miller", "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson",
    "White",
]

STREETS = [
    "123 Oak Street", "456 Maple Avenue", "789 Pine Road", "321 Elm Drive",
    "654 Cedar Lane", "987 Birch Boulevard", "147 Walnut Way",
    "258 Spruce Court", "369 Ash Place", "741 Willow Circle",
]

CITIES = [
    "Springfield", "Riverside", "Lakewood", "Fairview", "Georgetown",
    "Madison", "Burlington", "Clinton", "Franklin", "Greenville",
]

CARRIER_NAMES = ["FastTrack Logistics", "SpeedPost Express", "SwiftShip Co", "ReliableRoute Delivery"]

POLICY_TEXT = """# Delivery & Refund Policy

## Section 3.1 — Delivery Terms
All orders are shipped within 2 business days of payment confirmation.
Estimated delivery time is 5-10 business days from dispatch.
Signature may be required for orders over $100.

## Section 4.2 — Dispute Resolution
Customers must report non-receipt within 30 days of expected delivery.
Refund requests for services must be filed within 14 days of service date.

## Section 5.1 — Refund Policy
Full refunds are processed within 5-7 business days of approval.
Partial refunds may be issued for partially delivered services.
Duplicate charges are refunded automatically upon verification.
"""


def _rand_id(prefix: str, length: int = 8) -> str:
    return f"{prefix}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=length))}"


def _rand_amount() -> float:
    return round(random.uniform(15.0, 500.0), 2)


def _rand_datetime(base: datetime, offset_days_range: tuple[int, int]) -> datetime:
    delta = timedelta(days=random.randint(*offset_days_range), hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return base + delta


def _rand_address() -> str:
    return f"{random.choice(STREETS)}, {random.choice(CITIES)}"


def _rand_name() -> str:
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def _rand_tracking() -> str:
    return _rand_id("TRK", 12)


# ── Artifact Generators ───────────────────────────────────────────────────────

def _gen_order_record(case_id: str, order_id: str, customer_name: str,
                      address: str, amount: float, order_date: datetime) -> dict:
    return {
        "filename": f"{case_id}_order.json",
        "artifact_type": "order_record",
        "content": json.dumps({
            "order_id": order_id,
            "customer_name": customer_name,
            "shipping_address": address,
            "billing_address": address,
            "items": [
                {"name": f"Product {random.randint(100,999)}", "qty": random.randint(1, 3),
                 "unit_price": round(amount / random.randint(1, 3), 2)}
            ],
            "total_amount": amount,
            "currency": "USD",
            "order_date": order_date.isoformat(),
            "status": "confirmed",
        }, indent=2),
    }


def _gen_payment_record(case_id: str, txn_id: str, order_id: str,
                        amount: float, payment_date: datetime, suffix: str = "") -> dict:
    return {
        "filename": f"{case_id}_payment{suffix}.json",
        "artifact_type": "payment_record",
        "content": json.dumps({
            "transaction_id": txn_id,
            "order_id": order_id,
            "amount": amount,
            "currency": "USD",
            "payment_method": random.choice(["credit_card", "debit_card", "paypal"]),
            "status": "completed",
            "processed_at": payment_date.isoformat(),
        }, indent=2),
    }


def _gen_courier_log(case_id: str, tracking_id: str, address: str,
                     dispatch_date: datetime, delivery_date: datetime | None,
                     delivered: bool = True) -> dict:
    events = [
        {"timestamp": dispatch_date.isoformat(), "event": "package_dispatched",
         "location": "Warehouse A", "details": f"Tracking: {tracking_id}"},
        {"timestamp": (dispatch_date + timedelta(days=1)).isoformat(), "event": "in_transit",
         "location": "Sorting Facility", "details": "Package scanned"},
    ]
    if delivered and delivery_date:
        events.append({
            "timestamp": delivery_date.isoformat(), "event": "delivered",
            "location": address, "details": f"Signed by: {_rand_name()}",
        })
    elif delivery_date:
        events.append({
            "timestamp": delivery_date.isoformat(), "event": "delivery_attempted",
            "location": address, "details": "No one available",
        })
    return {
        "filename": f"{case_id}_courier_log.json",
        "artifact_type": "courier_log",
        "content": json.dumps({
            "tracking_id": tracking_id,
            "carrier": random.choice(CARRIER_NAMES),
            "destination_address": address,
            "events": events,
        }, indent=2),
    }


def _gen_chat_transcript(case_id: str, customer_name: str,
                         messages: list[dict]) -> dict:
    lines = [f"=== Chat Transcript — Case {case_id} ===", ""]
    for msg in messages:
        lines.append(f"[{msg['ts']}] {msg['sender']}: {msg['text']}")
    lines.append("\n=== End of Transcript ===")
    return {
        "filename": f"{case_id}_chat.txt",
        "artifact_type": "chat_transcript",
        "content": "\n".join(lines),
    }


def _gen_policy_doc(case_id: str) -> dict:
    return {
        "filename": f"{case_id}_policy.md",
        "artifact_type": "policy_text",
        "content": POLICY_TEXT,
    }


def _gen_refund_record(case_id: str, refund_id: str, txn_id: str | None,
                       amount: float, refund_date: datetime) -> dict:
    rec = {
        "refund_id": refund_id,
        "amount": amount,
        "currency": "USD",
        "status": "processed",
        "processed_at": refund_date.isoformat(),
    }
    if txn_id:
        rec["original_transaction_id"] = txn_id
    return {
        "filename": f"{case_id}_refund.json",
        "artifact_type": "refund_record",
        "content": json.dumps(rec, indent=2),
    }


def _gen_usage_log(case_id: str, service_start: datetime,
                   service_end: datetime | None, has_activity: bool = True) -> dict:
    entries = []
    if has_activity:
        current = service_start
        for i in range(random.randint(3, 8)):
            entries.append({
                "timestamp": current.isoformat(),
                "action": random.choice(["login", "api_call", "download", "stream", "query"]),
                "details": f"Session {i + 1}",
            })
            current += timedelta(hours=random.randint(1, 48))
    return {
        "filename": f"{case_id}_usage_log.json",
        "artifact_type": "usage_log",
        "content": json.dumps({
            "service_period_start": service_start.isoformat(),
            "service_period_end": service_end.isoformat() if service_end else None,
            "entries": entries,
        }, indent=2),
    }


def _gen_completion_notice(case_id: str, completion_date: datetime,
                           service_desc: str) -> dict:
    return {
        "filename": f"{case_id}_completion.json",
        "artifact_type": "completion_notice",
        "content": json.dumps({
            "completion_date": completion_date.isoformat(),
            "service_description": service_desc,
            "status": "completed",
            "verified_by": _rand_name(),
        }, indent=2),
    }


# ── Case Generators by Reason ────────────────────────────────────────────────

def _gen_pnr_case(case_id: str, inject_contradictions: list[str]) -> dict:
    """Product Not Received case."""
    base_date = datetime(2025, 1, 15) + timedelta(days=random.randint(0, 300))
    amount = _rand_amount()
    customer_name = _rand_name()
    order_address = _rand_address()
    order_id = _rand_id("ORD")
    txn_id = _rand_id("TXN")
    tracking_id = _rand_tracking()

    order_date = base_date
    payment_date = base_date + timedelta(hours=random.randint(0, 4))
    dispatch_date = base_date + timedelta(days=random.randint(1, 3))
    delivery_date = dispatch_date + timedelta(days=random.randint(3, 8))
    dispute_date = delivery_date + timedelta(days=random.randint(1, 10))
    deadline = dispute_date + timedelta(days=random.randint(5, 30))

    delivery_address = order_address
    delivered = random.random() > 0.3

    seeded_contradiction_ids = []

    # C1: delivery_before_dispatch
    if "C1" in inject_contradictions:
        delivery_date = dispatch_date - timedelta(days=random.randint(1, 3))
        seeded_contradiction_ids.append("C1")

    # C2: address_mismatch
    if "C2" in inject_contradictions:
        delivery_address = _rand_address()
        while delivery_address == order_address:
            delivery_address = _rand_address()
        seeded_contradiction_ids.append("C2")

    # C6: evidence_after_dispute_deadline
    if "C6" in inject_contradictions:
        delivery_date = deadline + timedelta(days=random.randint(1, 5))
        seeded_contradiction_ids.append("C6")

    chat_messages = [
        {"ts": dispute_date.isoformat(), "sender": customer_name,
         "text": f"Hi, I never received my order {order_id}. It's been over a week since the expected delivery."},
        {"ts": (dispute_date + timedelta(hours=2)).isoformat(), "sender": "Support Agent",
         "text": f"I'm sorry to hear that. Let me check tracking {tracking_id} for you."},
        {"ts": (dispute_date + timedelta(hours=3)).isoformat(), "sender": "Support Agent",
         "text": f"Our records show the package was {'delivered to ' + delivery_address if delivered else 'not yet delivered'}."},
        {"ts": (dispute_date + timedelta(hours=4)).isoformat(), "sender": customer_name,
         "text": "I'm at " + order_address + " and I definitely did not receive anything."},
    ]

    merchant_error = random.random() < 0.1  # 10% are genuine merchant errors

    artifacts = [
        _gen_order_record(case_id, order_id, customer_name, order_address, amount, order_date),
        _gen_payment_record(case_id, txn_id, order_id, amount, payment_date),
        _gen_courier_log(case_id, tracking_id, delivery_address, dispatch_date, delivery_date, delivered),
        _gen_chat_transcript(case_id, customer_name, chat_messages),
        _gen_policy_doc(case_id),
    ]

    # Expected facts for labels
    expected_facts = [
        {"type": "order", "description": f"Order {order_id} for ${amount}"},
        {"type": "payment", "description": f"Payment {txn_id} for ${amount}"},
        {"type": "courier_event", "description": f"Dispatch on {dispatch_date.date()}"},
    ]
    if delivered:
        expected_facts.append({"type": "courier_event", "description": f"Delivery on {delivery_date.date()}"})
        expected_facts.append({"type": "completion_notice", "description": "Delivery completed"})

    # Determine expected recommendation
    if merchant_error:
        expected_rec = "accept"
    elif seeded_contradiction_ids and any(c in ["C1", "C2"] for c in seeded_contradiction_ids):
        expected_rec = "escalate"
    elif delivered and not seeded_contradiction_ids:
        expected_rec = "challenge"
    else:
        expected_rec = "escalate"

    return {
        "case": {
            "id": case_id,
            "reason": "product_not_received",
            "amount": amount,
            "currency": "USD",
            "merchant_name": random.choice(MERCHANT_NAMES),
            "customer_id": _rand_id("CUST"),
            "created_at": dispute_date.isoformat(),
            "deadline": deadline.isoformat(),
            "artifacts": artifacts,
            "merchant_error": merchant_error,
        },
        "label": {
            "case_id": case_id,
            "expected_facts": expected_facts,
            "seeded_contradiction_ids": seeded_contradiction_ids,
            "expected_recommendation": expected_rec,
            "merchant_error": merchant_error,
        },
    }


def _gen_dup_case(case_id: str, inject_contradictions: list[str]) -> dict:
    """Duplicate Charge case."""
    base_date = datetime(2025, 1, 15) + timedelta(days=random.randint(0, 300))
    amount = _rand_amount()
    customer_name = _rand_name()
    address = _rand_address()
    order_id = _rand_id("ORD")
    txn_id_1 = _rand_id("TXN")
    txn_id_2 = _rand_id("TXN")
    order_date = base_date
    payment_date_1 = base_date + timedelta(hours=random.randint(0, 2))
    payment_date_2 = base_date + timedelta(hours=random.randint(3, 12))
    dispute_date = payment_date_2 + timedelta(days=random.randint(2, 14))
    deadline = dispute_date + timedelta(days=random.randint(5, 30))

    is_true_duplicate = random.random() < 0.4  # 40% are actually duplicates
    refund_issued = random.random() < 0.3
    seeded_contradiction_ids = []

    if is_true_duplicate:
        txn_id_2 = txn_id_1  # Same txn ID = true duplicate

    # C3: refund_unlinked_to_transaction
    if "C3" in inject_contradictions and refund_issued:
        seeded_contradiction_ids.append("C3")

    # C5: duplicate_claim_without_second_settlement
    if "C5" in inject_contradictions:
        seeded_contradiction_ids.append("C5")

    second_order_id = _rand_id("ORD") if not is_true_duplicate else order_id

    chat_messages = [
        {"ts": dispute_date.isoformat(), "sender": customer_name,
         "text": f"I was charged twice for order {order_id}! Transactions {txn_id_1} and {txn_id_2}."},
        {"ts": (dispute_date + timedelta(hours=1)).isoformat(), "sender": "Support Agent",
         "text": "Let me review both charges for you."},
        {"ts": (dispute_date + timedelta(hours=2)).isoformat(), "sender": "Support Agent",
         "text": f"I can see {'both charges reference the same order' if is_true_duplicate else 'these appear to be two separate orders'}."},
    ]

    artifacts = [
        _gen_order_record(case_id, order_id, customer_name, address, amount, order_date),
        _gen_payment_record(case_id, txn_id_1, order_id, amount, payment_date_1, "_1"),
        _gen_payment_record(case_id, txn_id_2, second_order_id, amount, payment_date_2, "_2"),
        _gen_chat_transcript(case_id, customer_name, chat_messages),
        _gen_policy_doc(case_id),
    ]

    if refund_issued:
        refund_txn = None if "C3" in seeded_contradiction_ids else txn_id_1
        artifacts.append(_gen_refund_record(
            case_id, _rand_id("REF"), refund_txn, amount,
            dispute_date + timedelta(days=random.randint(1, 5))
        ))

    expected_facts = [
        {"type": "order", "description": f"Order {order_id}"},
        {"type": "payment", "description": f"Payment 1: {txn_id_1}"},
        {"type": "payment", "description": f"Payment 2: {txn_id_2}"},
    ]

    if is_true_duplicate:
        expected_rec = "accept"
    elif seeded_contradiction_ids:
        expected_rec = "escalate"
    elif refund_issued:
        expected_rec = "accept"
    else:
        expected_rec = "challenge"

    return {
        "case": {
            "id": case_id,
            "reason": "duplicate_charge",
            "amount": amount,
            "currency": "USD",
            "merchant_name": random.choice(MERCHANT_NAMES),
            "customer_id": _rand_id("CUST"),
            "created_at": dispute_date.isoformat(),
            "deadline": deadline.isoformat(),
            "artifacts": artifacts,
            "merchant_error": is_true_duplicate,
        },
        "label": {
            "case_id": case_id,
            "expected_facts": expected_facts,
            "seeded_contradiction_ids": seeded_contradiction_ids,
            "expected_recommendation": expected_rec,
            "merchant_error": is_true_duplicate,
        },
    }


def _gen_snp_case(case_id: str, inject_contradictions: list[str]) -> dict:
    """Service Not Provided case."""
    base_date = datetime(2025, 1, 15) + timedelta(days=random.randint(0, 300))
    amount = _rand_amount()
    customer_name = _rand_name()
    order_id = _rand_id("ORD")
    txn_id = _rand_id("TXN")

    order_date = base_date
    payment_date = base_date + timedelta(hours=random.randint(0, 4))
    service_start = base_date + timedelta(days=random.randint(1, 3))
    service_end = service_start + timedelta(days=random.randint(7, 30))
    dispute_date = service_end + timedelta(days=random.randint(1, 10))
    deadline = dispute_date + timedelta(days=random.randint(5, 30))

    has_activity = random.random() > 0.3
    service_completed = random.random() > 0.3
    completion_date = service_end if service_completed else None
    seeded_contradiction_ids = []

    # C4: completion_notice_before_service_end
    if "C4" in inject_contradictions and service_completed:
        completion_date = service_start - timedelta(days=random.randint(1, 3))
        seeded_contradiction_ids.append("C4")

    # C6: evidence_after_dispute_deadline
    if "C6" in inject_contradictions:
        seeded_contradiction_ids.append("C6")

    service_desc = random.choice([
        "Premium subscription - monthly access",
        "Web development project - Phase 1",
        "Online course - Data Science Fundamentals",
        "Cloud hosting - Standard plan",
        "Consulting session - 2 hours",
    ])

    chat_messages = [
        {"ts": dispute_date.isoformat(), "sender": customer_name,
         "text": f"I paid for '{service_desc}' but the service was never provided."},
        {"ts": (dispute_date + timedelta(hours=2)).isoformat(), "sender": "Support Agent",
         "text": "I understand your concern. Let me check our service records."},
        {"ts": (dispute_date + timedelta(hours=3)).isoformat(), "sender": "Support Agent",
         "text": f"Our logs show {'some activity on your account' if has_activity else 'no activity on your account'} during the service period."},
    ]

    artifacts = [
        _gen_order_record(case_id, order_id, customer_name, _rand_address(), amount, order_date),
        _gen_payment_record(case_id, txn_id, order_id, amount, payment_date),
        _gen_usage_log(case_id, service_start, service_end, has_activity),
        _gen_chat_transcript(case_id, customer_name, chat_messages),
        _gen_policy_doc(case_id),
    ]

    if service_completed and completion_date:
        artifacts.append(_gen_completion_notice(case_id, completion_date, service_desc))

    expected_facts = [
        {"type": "order", "description": f"Order {order_id}"},
        {"type": "payment", "description": f"Payment {txn_id}"},
        {"type": "usage_log", "description": f"{'Has' if has_activity else 'No'} activity"},
    ]
    if service_completed:
        expected_facts.append({"type": "completion_notice", "description": "Service completed"})

    merchant_error = not has_activity and not service_completed

    if merchant_error:
        expected_rec = "accept"
    elif seeded_contradiction_ids:
        expected_rec = "escalate"
    elif has_activity and service_completed:
        expected_rec = "challenge"
    else:
        expected_rec = "escalate"

    return {
        "case": {
            "id": case_id,
            "reason": "service_not_provided",
            "amount": amount,
            "currency": "USD",
            "merchant_name": random.choice(MERCHANT_NAMES),
            "customer_id": _rand_id("CUST"),
            "created_at": dispute_date.isoformat(),
            "deadline": deadline.isoformat(),
            "artifacts": artifacts,
            "merchant_error": merchant_error,
        },
        "label": {
            "case_id": case_id,
            "expected_facts": expected_facts,
            "seeded_contradiction_ids": seeded_contradiction_ids,
            "expected_recommendation": expected_rec,
            "merchant_error": merchant_error,
        },
    }


# ── Main Generator ────────────────────────────────────────────────────────────

CONTRADICTION_MAP = {
    "product_not_received": ["C1", "C2", "C6"],
    "duplicate_charge": ["C3", "C5", "C6"],
    "service_not_provided": ["C4", "C6"],
}

GENERATOR_MAP = {
    "product_not_received": _gen_pnr_case,
    "duplicate_charge": _gen_dup_case,
    "service_not_provided": _gen_snp_case,
}


def generate_all_cases(seed: int = SEED, num_cases: int = NUM_CASES) -> dict:
    """Generate all synthetic cases and labels."""
    random.seed(seed)

    cases = []
    labels = []

    for i in range(num_cases):
        case_id = f"CASE-{i + 1:04d}"
        reason = random.choices(REASONS, weights=REASON_WEIGHTS, k=1)[0]

        # Decide whether to inject contradictions
        inject = []
        if random.random() < CONTRADICTION_RATE:
            available = CONTRADICTION_MAP[reason]
            num_contradictions = random.randint(1, min(2, len(available)))
            inject = random.sample(available, num_contradictions)

        gen_func = GENERATOR_MAP[reason]
        result = gen_func(case_id, inject)
        cases.append(result["case"])
        labels.append(result["label"])

    # Split into train/test
    indices = list(range(num_cases))
    random.shuffle(indices)
    test_count = int(num_cases * TEST_SPLIT_RATIO)
    test_indices = set(indices[:test_count])

    train_cases = [c for i, c in enumerate(cases) if i not in test_indices]
    test_cases = [c for i, c in enumerate(cases) if i in test_indices]
    train_labels = [l for i, l in enumerate(labels) if i not in test_indices]
    test_labels = [l for i, l in enumerate(labels) if i in test_indices]

    return {
        "all_cases": cases,
        "all_labels": labels,
        "train_cases": train_cases,
        "test_cases": test_cases,
        "train_labels": train_labels,
        "test_labels": test_labels,
    }


def write_cases(output_dir: str | Path | None = None) -> None:
    """Generate and write cases to disk."""
    if output_dir is None:
        output_dir = Path(__file__).parent

    output_dir = Path(output_dir)
    cases_dir = output_dir / "cases"
    labels_dir = output_dir / "labels"
    cases_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    data = generate_all_cases()

    # Write individual case files
    for case in data["all_cases"]:
        case_path = cases_dir / f"{case['id']}.json"
        with open(case_path, "w") as f:
            json.dump(case, f, indent=2)

    # Write individual label files
    for label in data["all_labels"]:
        label_path = labels_dir / f"{label['case_id']}.json"
        with open(label_path, "w") as f:
            json.dump(label, f, indent=2)

    # Write split metadata
    split_meta = {
        "seed": SEED,
        "total_cases": len(data["all_cases"]),
        "train_ids": [c["id"] for c in data["train_cases"]],
        "test_ids": [c["id"] for c in data["test_cases"]],
    }
    with open(output_dir / "split.json", "w") as f:
        json.dump(split_meta, f, indent=2)

    # Summary stats
    reasons_count = {}
    contradiction_count = 0
    for label in data["all_labels"]:
        r = [c["reason"] for c in data["all_cases"] if c["id"] == label["case_id"]][0]
        reasons_count[r] = reasons_count.get(r, 0) + 1
        if label["seeded_contradiction_ids"]:
            contradiction_count += 1

    print(f"Generated {len(data['all_cases'])} cases:")
    for r, c in sorted(reasons_count.items()):
        print(f"  {r}: {c}")
    print(f"Cases with contradictions: {contradiction_count}")
    print(f"Train: {len(data['train_cases'])}, Test: {len(data['test_cases'])}")
    print(f"Written to: {output_dir}")


if __name__ == "__main__":
    write_cases()
