"""
Fact Extractor — turns raw artifacts into structured Facts.

Uses LLM via json_guard for extraction. On failure, loads pre-extracted
fixture for that case. Preserves verbatim values for dates, amounts, and IDs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.contracts import CaseArtifact, Fact, FactType
from app.llm.base import LLMClient
from app.llm.json_guard import guarded_llm_call
from app.pii import safe_log

logger = logging.getLogger(__name__)

_FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "cases"

EXTRACTION_SYSTEM_PROMPT = """You are a precise fact extractor for payment dispute evidence.
Given a raw evidence artifact, extract ALL relevant facts as a JSON array.

Each fact must have:
- "id": sequential like "E1", "E2", etc. (will be renumbered later)
- "type": one of: order, payment, courier_event, chat_message, policy_clause, refund, usage_log, completion_notice
- "ts": ISO-8601 timestamp if available, null otherwise
- "text": short, faithful description of the fact
- "fields": dict of normalized values (amount, address, tracking_id, order_id, transaction_id, etc.)
- "source": artifact filename + locator (e.g. "order.json:root", "chat.txt:line5")
- "confidence": 0.0 to 1.0

Rules:
- Preserve EXACT values for dates, amounts, and IDs — do NOT infer or round
- Extract ALL facts, not just the most important
- Do NOT add information not present in the artifact
- Return ONLY a JSON array, no other text
"""


async def extract_facts(
    artifacts: list[CaseArtifact],
    llm_client: LLMClient,
    case_id: str = "",
    start_id: int = 1,
) -> list[Fact]:
    """
    Extract structured facts from raw case artifacts.

    Args:
        artifacts: List of raw evidence artifacts.
        llm_client: LLM client for extraction.
        case_id: Case ID for fixture fallback.
        start_id: Starting ID counter for fact numbering.

    Returns:
        List of validated Fact objects.
    """
    all_facts: list[Fact] = []
    fact_counter = start_id

    for artifact in artifacts:
        try:
            facts = await _extract_from_artifact(
                artifact, llm_client, fact_counter
            )
            all_facts.extend(facts)
            fact_counter += len(facts)
        except Exception as e:
            logger.warning(safe_log(
                f"Extraction failed for {artifact.filename}, using fixture fallback",
                error=str(e)[:200],
            ))
            facts = _fixture_fallback(artifact, fact_counter)
            all_facts.extend(facts)
            fact_counter += len(facts)

    # Renumber all facts sequentially
    for i, fact in enumerate(all_facts):
        fact.id = f"E{i + 1}"

    logger.info(safe_log(f"Extracted {len(all_facts)} facts from {len(artifacts)} artifacts"))
    return all_facts


async def _extract_from_artifact(
    artifact: CaseArtifact,
    llm_client: LLMClient,
    start_id: int,
) -> list[Fact]:
    """Extract facts from a single artifact using LLM."""
    messages = [
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Extract facts from this {artifact.artifact_type} artifact "
                f"(filename: {artifact.filename}):\n\n{artifact.content}"
            ),
        },
    ]

    result = await guarded_llm_call(
        client=llm_client,
        messages=messages,
        response_list_model=Fact,
        fallback_fn=lambda: _fixture_fallback(artifact, start_id),
    )

    if isinstance(result, list):
        return result
    return [result] if isinstance(result, Fact) else []


def _fixture_fallback(artifact: CaseArtifact, start_id: int) -> list[Fact]:
    """
    Deterministic fact extraction without LLM.
    Parses known artifact formats directly.
    """
    facts: list[Fact] = []
    counter = start_id

    try:
        if artifact.artifact_type in ("order_record", "order"):
            facts.extend(_parse_order(artifact, counter))
        elif artifact.artifact_type in ("payment_record", "payment"):
            facts.extend(_parse_payment(artifact, counter))
        elif artifact.artifact_type == "courier_log":
            facts.extend(_parse_courier_log(artifact, counter))
        elif artifact.artifact_type == "chat_transcript":
            facts.extend(_parse_chat(artifact, counter))
        elif artifact.artifact_type in ("policy_text", "policy"):
            facts.extend(_parse_policy(artifact, counter))
        elif artifact.artifact_type in ("refund_record", "refund"):
            facts.extend(_parse_refund(artifact, counter))
        elif artifact.artifact_type == "usage_log":
            facts.extend(_parse_usage_log(artifact, counter))
        elif artifact.artifact_type == "completion_notice":
            facts.extend(_parse_completion(artifact, counter))
    except Exception as e:
        logger.error(safe_log(f"Fixture fallback also failed for {artifact.filename}", error=str(e)[:200]))

    return facts


def _parse_order(artifact: CaseArtifact, start: int) -> list[Fact]:
    data = json.loads(artifact.content)
    return [Fact(
        id=f"E{start}",
        type=FactType.ORDER,
        ts=data.get("order_date"),
        text=f"Order {data.get('order_id', 'unknown')} placed for ${data.get('total_amount', 0)}",
        fields={
            "order_id": data.get("order_id", ""),
            "amount": data.get("total_amount", 0),
            "address": data.get("shipping_address", ""),
            "customer_name": data.get("customer_name", ""),
        },
        source=f"{artifact.filename}:root",
        confidence=0.95,
    )]


def _parse_payment(artifact: CaseArtifact, start: int) -> list[Fact]:
    data = json.loads(artifact.content)
    return [Fact(
        id=f"E{start}",
        type=FactType.PAYMENT,
        ts=data.get("processed_at"),
        text=f"Payment {data.get('transaction_id', 'unknown')} of ${data.get('amount', 0)} processed",
        fields={
            "transaction_id": data.get("transaction_id", ""),
            "amount": data.get("amount", 0),
            "order_id": data.get("order_id", ""),
        },
        source=f"{artifact.filename}:root",
        confidence=0.95,
    )]


def _parse_courier_log(artifact: CaseArtifact, start: int) -> list[Fact]:
    data = json.loads(artifact.content)
    facts = []
    counter = start
    tracking_id = data.get("tracking_id", "")
    dest_address = data.get("destination_address", "")

    for i, event in enumerate(data.get("events", [])):
        facts.append(Fact(
            id=f"E{counter}",
            type=FactType.COURIER_EVENT,
            ts=event.get("timestamp"),
            text=f"{event.get('event', 'unknown')} at {event.get('location', 'unknown')}",
            fields={
                "tracking_id": tracking_id,
                "event": event.get("event", ""),
                "location": event.get("location", ""),
                "address": dest_address if event.get("event") in ("delivered", "delivery_attempted") else "",
            },
            source=f"{artifact.filename}:events[{i}]",
            confidence=0.90,
        ))
        counter += 1

    return facts


def _parse_chat(artifact: CaseArtifact, start: int) -> list[Fact]:
    facts = []
    counter = start
    for i, line in enumerate(artifact.content.split("\n")):
        line = line.strip()
        if line.startswith("[") and "]" in line:
            # Parse "[timestamp] sender: message" format
            ts_end = line.index("]")
            ts = line[1:ts_end].strip()
            rest = line[ts_end + 1:].strip()
            if ":" in rest:
                sender, text = rest.split(":", 1)
                facts.append(Fact(
                    id=f"E{counter}",
                    type=FactType.CHAT_MESSAGE,
                    ts=ts if "T" in ts else None,
                    text=f"{sender.strip()}: {text.strip()}"[:200],
                    fields={"sender": sender.strip()},
                    source=f"{artifact.filename}:line{i + 1}",
                    confidence=0.85,
                ))
                counter += 1

    return facts


def _parse_policy(artifact: CaseArtifact, start: int) -> list[Fact]:
    """Extract policy clauses from markdown policy text."""
    facts = []
    counter = start
    current_section = ""

    for line in artifact.content.split("\n"):
        line = line.strip()
        if line.startswith("## "):
            current_section = line[3:].strip()
        elif line and not line.startswith("#") and current_section:
            facts.append(Fact(
                id=f"E{counter}",
                type=FactType.POLICY_CLAUSE,
                ts=None,
                text=f"{current_section}: {line}"[:200],
                fields={"section": current_section},
                source=f"{artifact.filename}:{current_section}",
                confidence=0.95,
            ))
            counter += 1

    return facts


def _parse_refund(artifact: CaseArtifact, start: int) -> list[Fact]:
    data = json.loads(artifact.content)
    fields: dict[str, Any] = {
        "refund_id": data.get("refund_id", ""),
        "amount": data.get("amount", 0),
    }
    if "original_transaction_id" in data:
        fields["transaction_id"] = data["original_transaction_id"]

    return [Fact(
        id=f"E{start}",
        type=FactType.REFUND,
        ts=data.get("processed_at"),
        text=f"Refund {data.get('refund_id', 'unknown')} of ${data.get('amount', 0)} processed",
        fields=fields,
        source=f"{artifact.filename}:root",
        confidence=0.95,
    )]


def _parse_usage_log(artifact: CaseArtifact, start: int) -> list[Fact]:
    data = json.loads(artifact.content)
    facts = []
    counter = start

    # Overall usage summary
    entries = data.get("entries", [])
    facts.append(Fact(
        id=f"E{counter}",
        type=FactType.USAGE_LOG,
        ts=data.get("service_period_start"),
        text=f"Usage log: {len(entries)} entries from {data.get('service_period_start', 'unknown')} to {data.get('service_period_end', 'unknown')}",
        fields={
            "entry_count": len(entries),
            "service_start": data.get("service_period_start", ""),
            "service_end": data.get("service_period_end", ""),
            "has_activity": len(entries) > 0,
        },
        source=f"{artifact.filename}:root",
        confidence=0.90,
    ))

    return facts


def _parse_completion(artifact: CaseArtifact, start: int) -> list[Fact]:
    data = json.loads(artifact.content)
    return [Fact(
        id=f"E{start}",
        type=FactType.COMPLETION_NOTICE,
        ts=data.get("completion_date"),
        text=f"Service completed: {data.get('service_description', 'unknown')}",
        fields={
            "completion_date": data.get("completion_date", ""),
            "service_description": data.get("service_description", ""),
        },
        source=f"{artifact.filename}:root",
        confidence=0.90,
    )]
