"""
Audit Trail storage — append-only record of system and human actions.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from app.contracts import AuditAction, AuditEvent
from app.storage.db import get_connection


def record_audit_event(
    case_id: str,
    action: AuditAction,
    actor: str = "system",
    payload: dict[str, Any] | None = None,
    conn: sqlite3.Connection | None = None,
) -> AuditEvent:
    """Record an audit event."""
    event = AuditEvent(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        case_id=case_id,
        action=action,
        actor=actor,
        timestamp=datetime.now(timezone.utc).isoformat(),
        payload=payload or {},
    )

    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        with conn:
            conn.execute(
                """
                INSERT INTO audit_events (id, case_id, action, actor, timestamp, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.case_id,
                    event.action.value if isinstance(event.action, AuditAction) else str(event.action),
                    event.actor,
                    event.timestamp,
                    json.dumps(event.payload),
                ),
            )
        return event
    finally:
        if should_close:
            conn.close()


def get_audit_trail(
    case_id: str,
    conn: sqlite3.Connection | None = None,
) -> list[AuditEvent]:
    """Retrieve full audit history for a given case, chronologically ordered."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    try:
        cur = conn.execute(
            "SELECT * FROM audit_events WHERE case_id = ? ORDER BY timestamp ASC",
            (case_id,),
        )
        rows = cur.fetchall()
        return [
            AuditEvent(
                id=r["id"],
                case_id=r["case_id"],
                action=AuditAction(r["action"]),
                actor=r["actor"],
                timestamp=r["timestamp"],
                payload=json.loads(r["payload_json"] or "{}"),
            )
            for r in rows
        ]
    finally:
        if should_close:
            conn.close()
