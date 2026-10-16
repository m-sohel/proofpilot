"""
Grounded Drafter — LLM writes prose from verified facts only.

The drafter receives ONLY the Fact list and the Decision.
The prompt forbids outside knowledge and requires JSON DraftSentence[] output.
"""

from __future__ import annotations

import logging

from app.contracts import (
    Decision,
    DraftSentence,
    Fact,
)
from app.drafting.template_fallback import build_template_draft
from app.llm.base import LLMClient
from app.llm.json_guard import guarded_llm_call

logger = logging.getLogger(__name__)


DRAFTER_SYSTEM_PROMPT = """You are a dispute response drafter. You write professional, evidence-grounded responses.

CRITICAL RULES:
1. You MUST use ONLY the facts provided below. NO outside knowledge.
2. Every claim sentence MUST reference at least one evidence ID (e.g., "E1", "E2").
3. Do NOT invent any dates, amounts, IDs, or names that are not in the provided facts.
4. Do NOT use words like "guaranteed", "will definitely", "certain to win", or absolute promises.
5. Use "estimate" instead of "prediction" or "chance" when referring to probabilities.
6. Be concise, professional, and factual.

Return a JSON array of objects, each with:
- "text": the sentence text
- "evidence_ids": array of fact IDs this sentence is based on (e.g., ["E1", "E2"])
- "kind": "claim" if the sentence makes a factual assertion, "boilerplate" if it's procedural/polite text

Boilerplate sentences (greetings, closings, procedural requests) may have empty evidence_ids.
Claim sentences MUST have at least one evidence_id.
"""


async def draft_response(
    facts: list[Fact],
    decision: Decision,
    llm_client: LLMClient,
    additional_constraints: list[str] | None = None,
) -> list[DraftSentence]:
    """
    Generate a grounded draft response using the LLM.

    Falls back to template if LLM fails.
    """
    facts_text = _format_facts_for_prompt(facts)
    decision_text = _format_decision_for_prompt(decision)

    user_content = (
        f"Write a dispute response based on these facts and decision.\n\n"
        f"FACTS:\n{facts_text}\n\n"
        f"DECISION:\n{decision_text}\n\n"
    )

    if additional_constraints:
        user_content += "ADDITIONAL CONSTRAINTS:\n"
        for constraint in additional_constraints:
            user_content += f"- {constraint}\n"
        user_content += "\n"

    user_content += "Return ONLY a JSON array of DraftSentence objects."

    messages = [
        {"role": "system", "content": DRAFTER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    result = await guarded_llm_call(
        client=llm_client,
        messages=messages,
        response_list_model=DraftSentence,
        fallback_fn=lambda: build_template_draft(facts, decision),
    )

    if isinstance(result, list):
        return result
    return build_template_draft(facts, decision)


def _format_facts_for_prompt(facts: list[Fact]) -> str:
    """Format facts for the LLM prompt."""
    lines = []
    for f in facts:
        fields_str = ", ".join(f"{k}={v}" for k, v in f.fields.items() if v)
        lines.append(
            f"[{f.id}] ({f.type.value}) {f.text} | ts={f.ts or 'N/A'} | {fields_str}"
        )
    return "\n".join(lines)


def _format_decision_for_prompt(decision: Decision) -> str:
    """Format decision for the LLM prompt."""
    return (
        f"Recommendation: {decision.recommendation.value}\n"
        f"Reasons: {'; '.join(decision.reasons)}\n"
        f"Evidence strength: {decision.evidence_strength:.0%}\n"
        f"Missing evidence: {', '.join(decision.missing_evidence) if decision.missing_evidence else 'None'}"
    )
