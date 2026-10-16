"""
SQLite database connection and schema initialization using stdlib sqlite3.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import get_config

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    reason TEXT NOT NULL,
    amount REAL NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL,
    deadline TEXT NOT NULL,
    merchant_name TEXT DEFAULT 'Merchant',
    customer_id TEXT DEFAULT '',
    merchant_error INTEGER NOT NULL DEFAULT 0,
    artifacts_json TEXT NOT NULL DEFAULT '[]',
    facts_json TEXT NOT NULL DEFAULT '[]',
    contradictions_json TEXT NOT NULL DEFAULT '[]',
    decision_json TEXT,
    draft_json TEXT NOT NULL DEFAULT '[]',
    grounding_report_json TEXT,
    redteam_findings_json TEXT NOT NULL DEFAULT '[]',
    approved_at TEXT,
    approved_by TEXT
);

CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'system',
    timestamp TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY(case_id) REFERENCES cases(id)
);

CREATE INDEX IF NOT EXISTS idx_audit_case_id ON audit_events(case_id);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
"""


def get_db_path(url_or_path: str | None = None) -> Path:
    """Resolve database URL or path to a local Path object."""
    if url_or_path is None:
        url_or_path = get_config().database_url

    if url_or_path.startswith("sqlite:///"):
        path_str = url_or_path[len("sqlite:///"):]
    elif url_or_path.startswith("sqlite://"):
        path_str = url_or_path[len("sqlite://"):]
    else:
        path_str = url_or_path

    p = Path(path_str)
    if not p.is_absolute():
        # Place relative to proofpilot project root
        root = Path(__file__).resolve().parent.parent.parent.parent
        p = root / path_str

    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Get a SQLite connection with Row factory enabled."""
    target_path = get_db_path(str(db_path)) if db_path is not None else get_db_path()
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str | Path | None = None) -> None:
    """Initialize SQLite schema."""
    conn = get_connection(db_path)
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
    finally:
        conn.close()
