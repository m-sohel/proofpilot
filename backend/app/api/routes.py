"""
ProofPilot REST API Endpoints.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.config import get_config
from app.contracts import (
    ApproveRequest,
    AuditAction,
    AuditEvent,
    CaseArtifact,
    CaseListResponse,
    CaseStatus,
    DisputeCase,
    DisputeReason,
    DraftEditRequest,
    HealthResponse,
    QueueItem,
    SeedResponse,
)
from app.decision.economics import make_decision
from app.decision.triage import compute_hours_left, rank_queue
from app.drafting.drafter import draft_response
from app.drafting.redteam import process_redteam_findings, run_redteam
from app.drafting.template_fallback import build_template_draft
from app.drafting.verifier import verify_draft
from app.evidence.contradictions import detect_contradictions
from app.extraction.extractor import extract_facts
from app.llm import get_llm_client
from app.pii import safe_log
from app.storage.audit import get_audit_trail, record_audit_event
from app.storage.repo import count_cases, get_case, list_cases, save_case

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """System health check and LLM connectivity status."""
    cfg = get_config()
    client = get_llm_client()
    try:
        is_avail = await client.is_available()
        llm_status = "ok" if is_avail else "unavailable"
    except Exception as e:
        logger.warning(safe_log(f"Health check LLM ping failed: {e}"))
        llm_status = "offline"

    return HealthResponse(
        status="ok",
        llm_status=llm_status,
        llm_provider=cfg.llm_provider,
        demo_mode=cfg.demo_mode,
    )


@router.post("/seed", response_model=SeedResponse)
async def seed_cases() -> SeedResponse:
    """Load seeded synthetic cases into the database."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    cases_dir = root_dir / "data" / "cases"

    if not cases_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seeded cases directory data/cases not found",
        )

    count = 0
    for case_file in cases_dir.glob("CASE-*.json"):
        try:
            with open(case_file, encoding="utf-8") as f:
                data = json.load(f)

            case = DisputeCase(
                id=data["id"],
                reason=DisputeReason(data["reason"]),
                amount=float(data["amount"]),
                currency=data.get("currency", "USD"),
                status=CaseStatus.NEW,
                created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
                deadline=data["deadline"],
                merchant_name=data.get("merchant_name", "Merchant"),
                customer_id=data.get("customer_id", ""),
                merchant_error=data.get("merchant_error", False),
                artifacts=[CaseArtifact(**a) for a in data.get("artifacts", [])],
            )
            save_case(case)
            record_audit_event(
                case_id=case.id,
                action=AuditAction.CREATED,
                actor="system",
                payload={"source": "seed", "filename": case_file.name},
            )
            count += 1
        except Exception as e:
            logger.error(safe_log(f"Failed to seed case from {case_file.name}: {e}"))

    return SeedResponse(
        cases_created=count,
        message=f"Successfully seeded {count} cases into database.",
    )


@router.get("/cases", response_model=CaseListResponse)
async def get_all_cases(
    status_filter: CaseStatus | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> CaseListResponse:
    """List disputes with optional status filter and pagination."""
    cases = list_cases(status=status_filter, limit=limit, offset=offset)
    total = count_cases()
    return CaseListResponse(cases=cases, total=total)


@router.post("/cases", response_model=DisputeCase, status_code=status.HTTP_201_CREATED)
async def create_case(case: DisputeCase) -> DisputeCase:
    """Create a new dispute case."""
    existing = get_case(case.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case with ID '{case.id}' already exists",
        )

    save_case(case)
    record_audit_event(
        case_id=case.id,
        action=AuditAction.CREATED,
        actor="user",
        payload={"amount": case.amount, "reason": case.reason.value},
    )
    return case


@router.get("/cases/{case_id}", response_model=DisputeCase)
async def get_case_by_id(case_id: str) -> DisputeCase:
    """Fetch complete dispute case details."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute case '{case_id}' not found",
        )
    return case


@router.get("/cases/{case_id}/audit", response_model=list[AuditEvent])
async def get_case_audit(case_id: str) -> list[AuditEvent]:
    """Retrieve complete audit history for a dispute case."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute case '{case_id}' not found",
        )
    return get_audit_trail(case_id)


@router.post("/cases/{case_id}/analyze", response_model=DisputeCase)
async def analyze_case(case_id: str) -> DisputeCase:
    """
    Run extraction, contradiction detection, and economics engine.
    Deterministic decision rules — LLM never picks recommendation.
    """
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")

    client = get_llm_client()

    # 1. Fact Extraction
    facts = await extract_facts(case.artifacts, client, case_id=case.id)
    case.facts = facts

    # 2. Contradiction Detection
    contradictions = detect_contradictions(facts, case.deadline)
    case.contradictions = contradictions

    # 3. Economics Engine Decision
    hours_left = compute_hours_left(case.deadline)
    decision = make_decision(
        facts=facts,
        contradictions=contradictions,
        amount=case.amount,
        hours_left=hours_left,
        reason=case.reason.value,
        merchant_error=case.merchant_error,
    )
    case.decision = decision
    case.status = CaseStatus.ANALYZED

    save_case(case)
    record_audit_event(
        case_id=case.id,
        action=AuditAction.ANALYZED,
        actor="system",
        payload={
            "facts_count": len(facts),
            "contradictions_count": len(contradictions),
            "recommendation": decision.recommendation.value,
            "net_ev": decision.economics.net_ev,
        },
    )
    return case


@router.post("/cases/{case_id}/draft", response_model=DisputeCase)
async def draft_case_response(case_id: str) -> DisputeCase:
    """
    Draft an evidence-grounded response and run the Grounding Verifier.
    'No evidence, no sentence'.
    """
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")

    if not case.decision or not case.facts:
        # Run analyze first if not analyzed
        case = await analyze_case(case_id)

    client = get_llm_client()
    cfg = get_config()

    if cfg.demo_mode or cfg.llm_provider == "mock":
        raw_draft = build_template_draft(case.facts, case.decision)
    else:
        raw_draft = await draft_response(case.facts, case.decision, client)

    # Enforce pure-code grounding verifier
    report = verify_draft(raw_draft, case.facts)
    case.draft = report.kept
    case.grounding_report = report
    case.status = CaseStatus.DRAFTED

    save_case(case)
    record_audit_event(
        case_id=case.id,
        action=AuditAction.DRAFTED,
        actor="system",
        payload={
            "kept_sentences": len(report.kept),
            "removed_sentences": len(report.removed),
            "todos_count": len(report.todos),
        },
    )
    return case


@router.post("/cases/{case_id}/redteam", response_model=DisputeCase)
async def redteam_case_draft(case_id: str) -> DisputeCase:
    """
    Run adversarial Issuer Red-Team pass on current draft.
    Applies deterministic code rules for patch/need_evidence/escalate.
    """
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")

    if not case.draft:
        case = await draft_case_response(case_id)

    client = get_llm_client()
    findings = await run_redteam(
        draft=case.draft,
        facts=case.facts,
        contradictions=case.contradictions,
        reason=case.reason.value,
        llm_client=client,
    )
    case.redteam_findings = findings

    if case.decision:
        updated_decision, patches, todos = process_redteam_findings(
            findings=findings,
            decision=case.decision,
            grounding_report=case.grounding_report,
        )
        case.decision = updated_decision

        # If patch requested and using LLM, execute at most 1 patch iteration
        if patches and not get_config().demo_mode and get_config().llm_provider != "mock":
            patched_draft = await draft_response(
                facts=case.facts,
                decision=case.decision,
                llm_client=client,
                additional_constraints=patches,
            )
            report = verify_draft(patched_draft, case.facts)
            case.draft = report.kept
            case.grounding_report = report

    save_case(case)
    record_audit_event(
        case_id=case.id,
        action=AuditAction.REDTEAMED,
        actor="system",
        payload={
            "findings_count": len(findings),
            "final_recommendation": case.decision.recommendation.value if case.decision else None,
        },
    )
    return case


@router.put("/cases/{case_id}/draft", response_model=DisputeCase)
async def update_case_draft(case_id: str, body: DraftEditRequest) -> DisputeCase:
    """Human edits the draft sentences; verifier re-checks grounding."""
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")

    if not body.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft cannot be empty",
        )

    # Re-verify edited draft against facts
    report = verify_draft(body.draft, case.facts)
    case.draft = report.kept
    case.grounding_report = report

    save_case(case)
    record_audit_event(
        case_id=case.id,
        action=AuditAction.EDITED,
        actor="human_reviewer",
        payload={
            "kept_sentences": len(report.kept),
            "removed_sentences": len(report.removed),
        },
    )
    return case


@router.post("/cases/{case_id}/approve", response_model=DisputeCase)
async def approve_case_response(case_id: str, req: ApproveRequest) -> DisputeCase:
    """
    Approve dispute response with explicit confirmation.
    Never auto-submits anything.
    """
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case '{case_id}' not found")

    if not req.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit confirmation required to approve response.",
        )

    if not req.approved_by.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer name / ID ('approved_by') must be provided.",
        )

    case.status = CaseStatus.APPROVED
    case.approved_at = datetime.now(timezone.utc).isoformat()
    case.approved_by = req.approved_by.strip()

    save_case(case)
    record_audit_event(
        case_id=case.id,
        action=AuditAction.APPROVED,
        actor=case.approved_by,
        payload={
            "approved_at": case.approved_at,
            "final_draft_length": len(case.draft),
            "recommendation": case.decision.recommendation.value if case.decision else None,
        },
    )
    return case


@router.get("/queue", response_model=list[QueueItem])
async def get_triage_queue() -> list[QueueItem]:
    """Retrieve deadline-aware ranked triage queue with score breakdown."""
    cases = list_cases(limit=500)
    # Filter or process all open/unapproved cases
    active_cases = [c for c in cases if c.status != CaseStatus.APPROVED]
    return rank_queue(active_cases)


@router.get("/benchmark")
async def get_benchmark_report(
    use_all: bool = Query(False, description="Evaluate full dataset vs 20% test split"),
) -> dict[str, Any]:
    """Run evaluation benchmark and compare against baselines."""
    from eval.run_benchmark import run_benchmark
    cfg = get_config()
    provider = "mock" if cfg.demo_mode else cfg.llm_provider
    result = await run_benchmark(use_all_cases=use_all, provider=provider)
    return result
