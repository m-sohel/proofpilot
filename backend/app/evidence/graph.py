"""
Evidence Graph — orders Facts into a timeline and links related facts.

Links facts by shared field values (order_id, transaction_id, tracking_id, address).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.contracts import Fact


@dataclass
class FactNode:
    """A fact in the evidence graph with links to related facts."""
    fact: Fact
    related_ids: list[str] = field(default_factory=list)
    ts_parsed: datetime | None = None


@dataclass
class EvidenceGraph:
    """Timeline-ordered evidence graph with cross-references."""
    nodes: list[FactNode]
    links: list[tuple[str, str, str]]  # (fact_id_a, fact_id_b, link_reason)


def build_evidence_graph(facts: list[Fact]) -> EvidenceGraph:
    """
    Build a timeline-ordered evidence graph from facts.

    1. Parse timestamps and sort chronologically (null timestamps go last).
    2. Link facts by shared field values.
    """
    # Build nodes with parsed timestamps
    nodes: list[FactNode] = []
    for fact in facts:
        ts_parsed = _parse_ts(fact.ts) if fact.ts else None
        nodes.append(FactNode(fact=fact, ts_parsed=ts_parsed))

    # Sort by timestamp (None goes to end)
    nodes.sort(key=lambda n: (n.ts_parsed is None, n.ts_parsed or datetime.max))

    # Find links between facts
    links = _find_links(facts)

    # Attach related IDs to nodes
    node_map = {n.fact.id: n for n in nodes}
    for a_id, b_id, reason in links:
        if a_id in node_map:
            node_map[a_id].related_ids.append(b_id)
        if b_id in node_map:
            node_map[b_id].related_ids.append(a_id)

    return EvidenceGraph(nodes=nodes, links=links)


def _find_links(facts: list[Fact]) -> list[tuple[str, str, str]]:
    """Find links between facts based on shared field values."""
    links: list[tuple[str, str, str]] = []
    link_fields = ["order_id", "transaction_id", "tracking_id"]

    # Build index: field_name -> value -> list of fact IDs
    index: dict[str, dict[Any, list[str]]] = {}
    for field_name in link_fields:
        index[field_name] = {}
        for fact in facts:
            val = fact.fields.get(field_name)
            if val and str(val).strip():
                index[field_name].setdefault(str(val), []).append(fact.id)

    # Generate links from shared values
    seen_pairs: set[tuple[str, str]] = set()
    for field_name, val_map in index.items():
        for val, fact_ids in val_map.items():
            for i, a in enumerate(fact_ids):
                for b in fact_ids[i + 1:]:
                    pair = (min(a, b), max(a, b))
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        links.append((a, b, f"shared_{field_name}"))

    # Also link facts with matching addresses
    address_index: dict[str, list[str]] = {}
    for fact in facts:
        addr = fact.fields.get("address", "")
        if addr and isinstance(addr, str) and len(addr) > 5:
            normalized = addr.lower().strip()
            address_index.setdefault(normalized, []).append(fact.id)

    for addr, fact_ids in address_index.items():
        for i, a in enumerate(fact_ids):
            for b in fact_ids[i + 1:]:
                pair = (min(a, b), max(a, b))
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    links.append((a, b, "shared_address"))

    return links


def _parse_ts(ts_str: str | None) -> datetime | None:
    """Parse an ISO-8601 timestamp string."""
    if not ts_str:
        return None
    try:
        # Handle various ISO-8601 formats
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        return None


def get_timeline(graph: EvidenceGraph) -> list[dict]:
    """
    Get a simple timeline representation for the frontend.
    """
    timeline = []
    for node in graph.nodes:
        timeline.append({
            "fact_id": node.fact.id,
            "type": node.fact.type.value,
            "ts": node.fact.ts,
            "text": node.fact.text,
            "related_ids": node.related_ids,
        })
    return timeline
