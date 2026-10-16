"""
Repository CRUD for DisputeCase entities.
"""

from __future__ import annotations

import json
import sqlite3

from app.contracts import (
    CaseArtifact,
    CaseStatus,
    Contradiction,
    Decision,
    DisputeCase,
    DisputeReason,
    DraftSentence,
    Fact,
    GroundingReport,
    RedTeamFinding,
)
from app.storage.db import get_connection


def save_case(case: DisputeCase, conn: sqlite3.Connection | None = None) -> None:
    """Insert or update a DisputeCase."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        with conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cases (
                    id, reason, amount, currency, status, created_at, deadline,
                    merchant_name, customer_id, merchant_error, artifacts_json, facts_json,
                    contradictions_json, decision_json, draft_json,
                    grounding_report_json, redteam_findings_json, approved_at, approved_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    case.id,
                    case.reason.value if isinstance(case.reason, DisputeReason) else str(case.reason),
                    case.amount,
                    case.currency,
                    case.status.value if isinstance(case.status, CaseStatus) else str(case.status),
                    case.created_at,
                    case.deadline,
                    case.merchant_name,
                    case.customer_id,
                    1 if case.merchant_error else 0,
                    json.dumps([a.model_dump() for a in case.artifacts]),
                    json.dumps([f.model_dump() for f in case.facts]),
                    json.dumps([c.model_dump() for c in case.contradictions]),
                    json.dumps(case.decision.model_dump()) if case.decision else None,
                    json.dumps([s.model_dump() for s in case.draft]),
                    json.dumps(case.grounding_report.model_dump()) if case.grounding_report else None,
                    json.dumps([rf.model_dump() for rf in case.redteam_findings]),
                    case.approved_at,
                    case.approved_by,
                ),
            )
    finally:
        if should_close:
            conn.close()


def get_case(case_id: str, conn: sqlite3.Connection | None = None) -> DisputeCase | None:
    """Fetch a single DisputeCase by ID."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        cur = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_case(row)
    finally:
        if should_close:
            conn.close()


def list_cases(
    status: CaseStatus | None = None,
    limit: int = 200,
    offset: int = 0,
    conn: sqlite3.Connection | None = None,
) -> list[DisputeCase]:
    """List dispute cases with optional status filter."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        if status:
            cur = conn.execute(
                "SELECT * FROM cases WHERE status = ? ORDER BY deadline ASC LIMIT ? OFFSET ?",
                (status.value if isinstance(status, CaseStatus) else str(status), limit, offset),
            )
        else:
            cur = conn.execute(
                "SELECT * FROM cases ORDER BY deadline ASC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        rows = cur.fetchall()
        return [_row_to_case(r) for r in rows]
    finally:
        if should_close:
            conn.close()


def count_cases(conn: sqlite3.Connection | None = None) -> int:
    """Total number of cases."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        cur = conn.execute("SELECT COUNT(*) FROM cases")
        return cur.fetchone()[0]
    finally:
        if should_close:
            conn.close()


def _row_to_case(row: sqlite3.Row) -> DisputeCase:
    """Convert a database row into a validated DisputeCase."""
    artifacts_data = json.loads(row["artifacts_json"] or "[]")
    facts_data = json.loads(row["facts_json"] or "[]")
    contr_data = json.loads(row["contradictions_json"] or "[]")
    decision_data = json.loads(row["decision_json"]) if row["decision_json"] else None
    draft_data = json.loads(row["draft_json"] or "[]")
    grounding_data = json.loads(row["grounding_report_json"]) if row["grounding_report_json"] else None
    redteam_data = json.loads(row["redteam_findings_json"] or "[]")

    return DisputeCase(
        id=row["id"],
        reason=DisputeReason(row["reason"]),
        amount=float(row["amount"]),
        currency=row["currency"],
        status=CaseStatus(row["status"]),
        created_at=row["created_at"],
        deadline=row["deadline"],
        merchant_name=row["merchant_name"] or "Merchant",
        customer_id=row["customer_id"] or "",
        merchant_error=bool(row["merchant_error"]) if "merchant_error" in row.keys() else False,
        artifacts=[CaseArtifact(**a) for a in artifacts_data],
        facts=[Fact(**f) for f in facts_data],
        contradictions=[Contradiction(**c) for c in contr_data],
        decision=Decision(**decision_data) if decision_data else None,
        draft=[DraftSentence(**s) for s in draft_data],
        grounding_report=GroundingReport(**grounding_data) if grounding_data else None,
        redteam_findings=[RedTeamFinding(**rf) for rf in redteam_data],
        approved_at=row["approved_at"],
        approved_by=row["approved_by"],
    )
