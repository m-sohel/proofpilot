"""
ProofPilot Contracts — Pydantic v2 models shared across all modules.

These are the single source of truth. Frontend TypeScript types must mirror these.
Do not change without updating both sides.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ── Enums ──────────────────────────────────────────────────────────────────────

class FactType(str, Enum):
    ORDER = "order"
    PAYMENT = "payment"
    COURIER_EVENT = "courier_event"
    CHAT_MESSAGE = "chat_message"
    POLICY_CLAUSE = "policy_clause"
    REFUND = "refund"
    USAGE_LOG = "usage_log"
    COMPLETION_NOTICE = "completion_notice"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Recommendation(str, Enum):
    ACCEPT = "accept"
    CHALLENGE = "challenge"
    ESCALATE = "escalate"


class SentenceKind(str, Enum):
    CLAIM = "claim"
    BOILERPLATE = "boilerplate"


class FixType(str, Enum):
    PATCH = "patch"
    NEED_EVIDENCE = "need_evidence"
    ESCALATE = "escalate"


class DisputeReason(str, Enum):
    PRODUCT_NOT_RECEIVED = "product_not_received"
    DUPLICATE_CHARGE = "duplicate_charge"
    SERVICE_NOT_PROVIDED = "service_not_provided"
    REFUND_NOT_PROCESSED = "refund_not_processed"


class CaseStatus(str, Enum):
    NEW = "new"
    ANALYZED = "analyzed"
    DRAFTED = "drafted"
    APPROVED = "approved"


class AuditAction(str, Enum):
    CREATED = "created"
    ANALYZED = "analyzed"
    DRAFTED = "drafted"
    REDTEAMED = "redteamed"
    EDITED = "edited"
    APPROVED = "approved"


# ── Core Models ────────────────────────────────────────────────────────────────

class Fact(BaseModel):
    """A single structured fact extracted from evidence."""
    id: str = Field(description="E.g. 'E1', 'E2', ...")
    type: FactType
    ts: str | None = Field(default=None, description="ISO-8601 timestamp or null")
    text: str = Field(description="Short, faithful description of the fact")
    fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Normalized values: amount, address, tracking_id, etc.",
    )
    source: str = Field(default="evidence", description="Artifact filename + locator")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)


class Contradiction(BaseModel):
    """A detected contradiction between evidence facts."""
    id: str
    rule_id: str = Field(description="E.g. 'C1', 'C2', ...")
    severity: Severity
    fact_ids: list[str]
    explanation: str


class Economics(BaseModel):
    """Financial breakdown for the dispute decision."""
    amount: float
    expected_recovery: float
    handling_cost: float
    dispute_fee: float
    net_ev: float


class Decision(BaseModel):
    """The deterministic recommendation for a dispute."""
    recommendation: Recommendation
    reasons: list[str]
    evidence_strength: float = Field(ge=0.0, le=1.0)
    p_win_estimate: float = Field(ge=0.0, le=1.0)
    economics: Economics
    missing_evidence: list[str] = Field(default_factory=list)
    hours_left: float
    requires_human_review: bool = Field(default=True)
    deadline_warning: str | None = None


class DraftSentence(BaseModel):
    """A single sentence in the dispute response draft."""
    text: str
    evidence_ids: list[str]
    kind: SentenceKind


class GroundingReport(BaseModel):
    """Result of verifying draft sentences against evidence."""
    kept: list[DraftSentence]
    removed: list[dict[str, str]] = Field(
        default_factory=list,
        description="Each has 'text' and 'reason'",
    )
    todos: list[str] = Field(default_factory=list)


class RedTeamFinding(BaseModel):
    """An adversarial finding from the issuer red-team pass."""
    weakness: str
    why_it_loses: str
    fix_type: FixType
    related_fact_ids: list[str] = Field(default_factory=list)


# ── Case & Queue Models ───────────────────────────────────────────────────────

class CaseArtifact(BaseModel):
    """A raw evidence artifact attached to a dispute case."""
    filename: str
    content: str
    artifact_type: str = Field(description="E.g. 'courier_log', 'chat_transcript'")


class DisputeCase(BaseModel):
    """A full dispute case with all analysis results."""
    id: str
    reason: DisputeReason
    amount: float
    currency: str = "USD"
    status: CaseStatus = CaseStatus.NEW
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    deadline: str = Field(description="ISO-8601 deadline for response")
    merchant_name: str = "Merchant"
    customer_id: str = ""
    merchant_error: bool = False
    artifacts: list[CaseArtifact] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    decision: Decision | None = None
    draft: list[DraftSentence] = Field(default_factory=list)
    grounding_report: GroundingReport | None = None
    redteam_findings: list[RedTeamFinding] = Field(default_factory=list)
    approved_at: str | None = None
    approved_by: str | None = None


class QueueItem(BaseModel):
    """A case in the triage queue with score breakdown."""
    case_id: str
    reason: DisputeReason
    amount: float
    hours_left: float
    recommendation: Recommendation | None = None
    score: float
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    is_overdue: bool = False
    deadline_warning: str | None = None


class AuditEvent(BaseModel):
    """An entry in the audit trail."""
    id: str
    case_id: str
    action: AuditAction
    actor: str = "system"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: dict[str, Any] = Field(default_factory=dict)


# ── API Request/Response Models ────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    llm_status: str = "unknown"
    llm_provider: str = "mock"
    demo_mode: bool = False


class SeedResponse(BaseModel):
    cases_created: int
    message: str = "Seeded successfully"


class CaseListResponse(BaseModel):
    cases: list[DisputeCase]
    total: int


class ErrorResponse(BaseModel):
    detail: str


class ApproveRequest(BaseModel):
    approved_by: str = Field(description="Name or ID of the human reviewer")
    confirm: bool = Field(default=False, description="Explicit confirmation to approve")


class DraftEditRequest(BaseModel):
    draft: list[DraftSentence]
