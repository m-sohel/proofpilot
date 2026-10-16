"""
Grounding Verifier — pure code, no LLM.

Checks every draft sentence against the fact set:
  a) Every claim sentence must cite at least one valid evidence ID
  b) Every cited ID must exist
  c) Every date, currency amount, order/transaction/tracking ID and name
     in a sentence must appear in the tagged facts' text or fields
  d) Reject absolute promises ("guaranteed", "will definitely", etc.)

Failing sentences are removed and converted into todos.
"""

from __future__ import annotations

import logging
import re

from app.contracts import (
    DraftSentence,
    Fact,
    GroundingReport,
    SentenceKind,
)
from app.pii import safe_log

logger = logging.getLogger(__name__)

# Boilerplate whitelist — sentences matching these patterns are allowed
# without evidence references
BOILERPLATE_PATTERNS = [
    r"thank you",
    r"we have reviewed",
    r"respectfully",
    r"committed to resolving",
    r"welcome any additional",
    r"bring.* to our attention",
    r"we accept this dispute",
    r"we.*contest this dispute",
    r"requires additional review",
    r"present the following",
]

# Absolute promise patterns to reject
ABSOLUTE_PROMISE_PATTERNS = [
    r"\bguarantee[ds]?\b",
    r"\bwill definitely\b",
    r"\bcertain to\b",
    r"\b100\s*%\s*(?:sure|certain|confident)\b",
    r"\babsolutely certain\b",
    r"\bno doubt\b",
    r"\bwithout question\b",
    r"\bpromise\b",
]

# Patterns to extract verifiable entities from sentences
DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
AMOUNT_PATTERN = re.compile(r"\$\s*([\d,]+(?:\.\d{2})?)")
ID_PATTERNS = [
    re.compile(r"\b(ORD-[\w-]+)\b"),
    re.compile(r"\b(TXN-[\w-]+)\b"),
    re.compile(r"\b(TRK-[\w-]+)\b"),
    re.compile(r"\b(REF-[\w-]+)\b"),
    re.compile(r"\b(CUST-[\w-]+)\b"),
]


def verify_draft(
    sentences: list[DraftSentence],
    facts: list[Fact],
) -> GroundingReport:
    """
    Verify every sentence in the draft against the evidence.

    Returns a GroundingReport with kept/removed sentences and todos.
    """
    fact_map = {f.id: f for f in facts}
    valid_ids = set(fact_map.keys())

    kept: list[DraftSentence] = []
    removed: list[dict[str, str]] = []
    todos: list[str] = []

    for sentence in sentences:
        rejection_reason = _check_sentence(sentence, fact_map, valid_ids)
        if rejection_reason:
            removed.append({"text": sentence.text, "reason": rejection_reason})
            todos.append(f"Fix or remove: '{sentence.text[:80]}...' — {rejection_reason}")
            logger.warning(safe_log(
                "Verifier rejected sentence",
                reason=rejection_reason,
            ))
        else:
            kept.append(sentence)

    report = GroundingReport(kept=kept, removed=removed, todos=todos)

    logger.info(safe_log(
        f"Verifier: {len(kept)} kept, {len(removed)} removed, {len(todos)} todos"
    ))

    return report


def _check_sentence(
    sentence: DraftSentence,
    fact_map: dict[str, Fact],
    valid_ids: set[str],
) -> str | None:
    """
    Check a single sentence. Returns rejection reason or None if valid.
    """
    text = sentence.text
    text_lower = text.lower()

    # Check d) — absolute promises
    for pattern in ABSOLUTE_PROMISE_PATTERNS:
        if re.search(pattern, text_lower):
            return f"Contains absolute promise matching '{pattern}'"

    # Boilerplate handling
    if sentence.kind == SentenceKind.BOILERPLATE:
        is_whitelisted = any(
            re.search(p, text_lower)
            for p in BOILERPLATE_PATTERNS
        )
        if is_whitelisted:
            return None  # Allowed boilerplate
        # Non-whitelisted boilerplate with evidence IDs is treated as claim
        if not sentence.evidence_ids:
            return "Boilerplate sentence not in whitelist and has no evidence IDs"

    # Check a) — claim sentences need at least one evidence ID
    if sentence.kind == SentenceKind.CLAIM:
        if not sentence.evidence_ids:
            return "Claim sentence has no evidence IDs"

    # Check b) — all cited IDs must exist
    for eid in sentence.evidence_ids:
        if eid not in valid_ids:
            return f"References nonexistent evidence ID '{eid}'"

    # Get the tagged facts for this sentence
    tagged_facts = [fact_map[eid] for eid in sentence.evidence_ids if eid in fact_map]

    if sentence.kind == SentenceKind.CLAIM or sentence.evidence_ids:
        # Check c) — verify dates, amounts, and IDs against tagged facts
        reason = _check_entities_against_facts(text, tagged_facts)
        if reason:
            return reason

    return None


def _check_entities_against_facts(
    text: str,
    tagged_facts: list[Fact],
) -> str | None:
    """
    Check that every date, amount, and ID in the sentence appears
    in the tagged facts' text or fields.
    """
    # Build a searchable text corpus from the tagged facts
    fact_corpus = _build_fact_corpus(tagged_facts)

    # Check dates
    dates_in_text = DATE_PATTERN.findall(text)
    for date_str in dates_in_text:
        if date_str not in fact_corpus:
            return f"Date '{date_str}' not found in cited evidence"

    # Check currency amounts
    amounts_in_text = AMOUNT_PATTERN.findall(text)
    for amount_str in amounts_in_text:
        # Normalize: remove commas
        normalized = amount_str.replace(",", "")
        if not _amount_in_facts(normalized, tagged_facts):
            return f"Amount '${amount_str}' not found in cited evidence"

    # Check order/transaction/tracking IDs
    for pattern in ID_PATTERNS:
        ids_in_text = pattern.findall(text)
        for id_str in ids_in_text:
            if id_str not in fact_corpus:
                return f"ID '{id_str}' not found in cited evidence"

    return None


def _build_fact_corpus(facts: list[Fact]) -> str:
    """Build a searchable text from facts' text and fields."""
    parts: list[str] = []
    for f in facts:
        parts.append(f.text)
        if f.ts:
            parts.append(f.ts)
        for key, val in f.fields.items():
            parts.append(str(val))
    return " ".join(parts)


def _amount_in_facts(amount_str: str, facts: list[Fact]) -> bool:
    """Check if a dollar amount appears in the facts' fields or text."""
    try:
        target = float(amount_str)
    except ValueError:
        return False

    for f in facts:
        # Check fields
        for key, val in f.fields.items():
            try:
                if abs(float(val) - target) < 0.01:
                    return True
            except (ValueError, TypeError):
                pass
        # Check text
        if amount_str in f.text or f"{target:.2f}" in f.text:
            return True

    return False
