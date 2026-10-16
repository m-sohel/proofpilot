"""
Mock LLM Client — deterministic fixtures for tests and demo.

Returns pre-built JSON responses so the pipeline works without any model.
"""

from __future__ import annotations

import json
from typing import Any

from app.llm.base import LLMClient

# ── Fixture responses keyed by prompt hint ─────────────────────────────────────

_EXTRACTION_FIXTURE = [
    {
        "id": "E1",
        "type": "order",
        "ts": "2025-03-15T10:30:00",
        "text": "Order ORD-FIXTURE01 placed for $125.00",
        "fields": {"order_id": "ORD-FIXTURE01", "amount": 125.00, "address": "123 Oak Street, Springfield"},
        "source": "order.json:root",
        "confidence": 0.95,
    },
    {
        "id": "E2",
        "type": "payment",
        "ts": "2025-03-15T10:35:00",
        "text": "Payment TXN-FIXTURE01 of $125.00 processed",
        "fields": {"transaction_id": "TXN-FIXTURE01", "amount": 125.00},
        "source": "payment.json:root",
        "confidence": 0.95,
    },
    {
        "id": "E3",
        "type": "courier_event",
        "ts": "2025-03-16T08:00:00",
        "text": "Package dispatched from Warehouse A, tracking TRK-FIXTURE01",
        "fields": {"tracking_id": "TRK-FIXTURE01", "event": "dispatched"},
        "source": "courier_log.json:events[0]",
        "confidence": 0.90,
    },
    {
        "id": "E4",
        "type": "courier_event",
        "ts": "2025-03-20T14:30:00",
        "text": "Package delivered to 123 Oak Street, Springfield",
        "fields": {"tracking_id": "TRK-FIXTURE01", "event": "delivered", "address": "123 Oak Street, Springfield"},
        "source": "courier_log.json:events[2]",
        "confidence": 0.90,
    },
    {
        "id": "E5",
        "type": "chat_message",
        "ts": "2025-03-22T09:00:00",
        "text": "Customer reports not receiving the order at 123 Oak Street, Springfield",
        "fields": {"address": "123 Oak Street, Springfield"},
        "source": "chat.txt:line3",
        "confidence": 0.85,
    },
    {
        "id": "E6",
        "type": "policy_clause",
        "ts": None,
        "text": "Delivery policy: signature required for orders over $100",
        "fields": {"threshold": 100.00},
        "source": "policy.md:section3.1",
        "confidence": 0.95,
    },
]

_DRAFT_FIXTURE = [
    {
        "text": "Order ORD-FIXTURE01 was placed on 2025-03-15 for $125.00 and shipped to 123 Oak Street, Springfield.",
        "evidence_ids": ["E1"],
        "kind": "claim",
    },
    {
        "text": "Payment TXN-FIXTURE01 of $125.00 was successfully processed on 2025-03-15.",
        "evidence_ids": ["E2"],
        "kind": "claim",
    },
    {
        "text": "Tracking record TRK-FIXTURE01 confirms the package was dispatched on 2025-03-16 and delivered to 123 Oak Street, Springfield on 2025-03-20.",
        "evidence_ids": ["E3", "E4"],
        "kind": "claim",
    },
    {
        "text": "We respectfully request the issuing bank to review the evidence provided and consider reversing the dispute.",
        "evidence_ids": [],
        "kind": "boilerplate",
    },
]

_REDTEAM_FIXTURE = [
    {
        "weakness": "No signature proof in delivery confirmation",
        "why_it_loses": "Issuer may argue delivery was to wrong person without signature verification",
        "fix_type": "need_evidence",
        "related_fact_ids": ["E4"],
    },
    {
        "weakness": "Customer explicitly states non-receipt",
        "why_it_loses": "Customer testimony contradicts carrier data; issuer may side with cardholder",
        "fix_type": "patch",
        "related_fact_ids": ["E4", "E5"],
    },
    {
        "weakness": "No photo proof of delivery",
        "why_it_loses": "Modern dispute processes often require visual evidence of delivery",
        "fix_type": "need_evidence",
        "related_fact_ids": ["E4"],
    },
]


class MockLLMClient(LLMClient):
    """
    Deterministic LLM client that returns fixture data.
    Used for tests and demos — guarantees reproducibility.
    """

    async def chat(
        self,
        messages: list[dict[str, str]],
        json_schema: dict[str, Any] | None = None,
        temperature: float = 0.1,
    ) -> str:
        # Determine what kind of response is needed from the prompt content
        prompt_text = " ".join(m.get("content", "") for m in messages).lower()

        if "extract" in prompt_text and "fact" in prompt_text:
            return json.dumps(_EXTRACTION_FIXTURE)
        elif "draft" in prompt_text or "response" in prompt_text and "sentence" in prompt_text:
            return json.dumps(_DRAFT_FIXTURE)
        elif "red" in prompt_text and "team" in prompt_text:
            return json.dumps(_REDTEAM_FIXTURE)
        else:
            # Generic fallback
            return json.dumps(_EXTRACTION_FIXTURE)

    async def is_available(self) -> bool:
        return True

    @property
    def provider_name(self) -> str:
        return "mock"
