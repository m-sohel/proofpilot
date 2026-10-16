"""
Issuer Red-Team — adversarial review of dispute response drafts.

Simulates how a bank / card issuer will scrutinize the merchant's response:
- Receives draft, facts, contradictions, and playbook failure modes
- Returns the top 3 RedTeamFindings
- Pure code processes the findings:
    * patch: regenerate draft once with finding as an added constraint (max 1 patch)
    * need_evidence: add finding to todos
    * escalate: override recommendation to escalate with the reason
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.contracts import (
    Contradiction,
    Decision,
    DraftSentence,
    Fact,
    FixType,
    GroundingReport,
    Recommendation,
    RedTeamFinding,
    Severity,
)
from app.decision.economics import load_playbook
from app.llm.base import LLMClient
from app.llm.json_guard import guarded_llm_call
from app.pii import safe_log

logger = logging.getLogger(__name__)

REDTEAM_SYSTEM_PROMPT = """You are an adversarial bank chargeback representative (Issuer Red-Team).
Your job is to scrutinize the merchant's dispute response draft and find why an issuer would reject it.

Evaluate the draft against:
- Stated facts and timestamps
- Known chargeback failure modes
- Evidentiary gaps and contradictions

Return a JSON array of up to 3 findings, ordered by severity.
Each finding must have:
- "weakness": concise title of the flaw
- "why_it_loses": explanation of why the cardholder/issuer will win despite this claim
- "fix_type": one of "patch" (draft wording can be tightened), "need_evidence" (merchant must produce missing proof), or "escalate" (fatal contradiction or error requiring manual escalation)
- "related_fact_ids": list of fact IDs involved

Return ONLY a JSON array, no other text.
"""


async def run_redteam(
    draft: list[DraftSentence],
    facts: list[Fact],
    contradictions: list[Contradiction],
    reason: str,
    llm_client: LLMClient,
) -> list[RedTeamFinding]:
    """
    Run adversarial red-team review on a draft.
    Uses LLM with fallback to deterministic rule-based analysis.
    """
    playbook = load_playbook(reason)
    known_failure_modes = playbook.get("known_failure_modes", [])

    prompt_payload = {
        "dispute_reason": reason,
        "draft": [{"text": s.text, "evidence_ids": s.evidence_ids} for s in draft],
        "facts": [{"id": f.id, "type": f.type.value, "text": f.text, "fields": f.fields} for f in facts],
        "contradictions": [
            {"id": c.id, "rule": c.rule_id, "severity": c.severity.value, "explanation": c.explanation}
            for c in contradictions
        ],
        "known_failure_modes": known_failure_modes,
    }

    user_prompt = f"Analyze this dispute response draft and return top 3 findings:\n{json.dumps(prompt_payload, indent=2)}"

    def fallback_factory() -> list[RedTeamFinding]:
        raw_list = _deterministic_redteam_analysis(draft, facts, contradictions, known_failure_modes)
        return [
            RedTeamFinding(
                weakness=f["weakness"],
                why_it_loses=f["why_it_loses"],
                fix_type=FixType(f["fix_type"]),
                related_fact_ids=f.get("related_fact_ids", []),
            )
            for f in raw_list[:3]
        ]

    messages = [
        {"role": "system", "content": REDTEAM_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        findings = await guarded_llm_call(
            client=llm_client,
            messages=messages,
            response_list_model=RedTeamFinding,
            fallback_fn=fallback_factory,
        )

        if not isinstance(findings, list):
            findings = [findings] if isinstance(findings, RedTeamFinding) else fallback_factory()

        findings = findings[:3]
        logger.info(safe_log(f"Red-team generated {len(findings)} findings"))
        return findings

    except Exception as e:
        logger.error(safe_log(f"Red-team execution failed, using fallback: {e}"))
        return fallback_factory()


def _deterministic_redteam_analysis(
    draft: list[DraftSentence],
    facts: list[Fact],
    contradictions: list[Contradiction],
    known_failure_modes: list[str],
) -> list[dict[str, Any]]:
    """Deterministic rule-based adversarial analysis when LLM is unavailable or fails."""
    findings: list[dict[str, Any]] = []

    # Check 1: Any high-severity contradiction is fatal
    high_contrs = [c for c in contradictions if c.severity == Severity.HIGH]
    if high_contrs:
        c = high_contrs[0]
        findings.append({
            "weakness": f"Fatal evidentiary conflict ({c.rule_id})",
            "why_it_loses": f"Issuer will uphold chargeback due to discrepancy: {c.explanation}",
            "fix_type": "escalate",
            "related_fact_ids": c.fact_ids,
        })

    # Check 2: Delivery without signature or photo proof
    delivery_facts = [f for f in facts if f.fields.get("event") == "delivered"]
    has_signature = any(
        "signature" in f.text.lower() or f.fields.get("signature")
        for f in facts
    )
    if delivery_facts and not has_signature:
        findings.append({
            "weakness": "Delivery confirmation lacks recipient signature",
            "why_it_loses": "Card issuer guidelines require positive proof of receipt; carrier scan alone may be disputed as porch theft.",
            "fix_type": "need_evidence",
            "related_fact_ids": [f.id for f in delivery_facts],
        })

    # Check 3: Check for draft sentences with unassertive wording
    for s in draft:
        if any(w in s.text.lower() for w in ["likely", "supposedly", "presumed", "appears to"]):
            findings.append({
                "weakness": f"Speculative language in response: '{s.text[:50]}...'",
                "why_it_loses": "Issuer arbitration penalizes ambiguous or hesitant merchant assertions.",
                "fix_type": "patch",
                "related_fact_ids": s.evidence_ids,
            })
            break

    # If still fewer than 3, add known failure modes if relevant
    if len(findings) < 3 and known_failure_modes:
        for mode in known_failure_modes:
            if len(findings) >= 3:
                break
            findings.append({
                "weakness": mode,
                "why_it_loses": f"Common issuer rejection reason for this dispute category: {mode}",
                "fix_type": "need_evidence",
                "related_fact_ids": [],
            })

    return findings


def process_redteam_findings(
    findings: list[RedTeamFinding],
    decision: Decision,
    grounding_report: GroundingReport | None = None,
) -> tuple[Decision, list[str], list[str]]:
    """
    Apply code rules to red-team findings.

    Returns:
        (updated_decision, patch_constraints, new_todos)
    """
    patch_constraints: list[str] = []
    new_todos: list[str] = []

    for f in findings:
        if f.fix_type == FixType.ESCALATE:
            decision.recommendation = Recommendation.ESCALATE
            decision.reasons.append(f"Issuer Red-Team Escalation: {f.weakness} — {f.why_it_loses}")
            logger.warning(safe_log(f"Red-team escalated decision: {f.weakness}"))

        elif f.fix_type == FixType.NEED_EVIDENCE:
            todo = f"Missing Evidence Required: {f.weakness} ({f.why_it_loses})"
            new_todos.append(todo)
            if grounding_report and todo not in grounding_report.todos:
                grounding_report.todos.append(todo)

        elif f.fix_type == FixType.PATCH:
            patch_constraints.append(f"Fix weakness: {f.weakness}. Ensure: {f.why_it_loses}")

    return decision, patch_constraints, new_todos
