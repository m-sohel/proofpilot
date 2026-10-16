"""
End-to-End Integration Test for ProofPilot.

Verifies complete lifecycle with LLM_PROVIDER=mock:
seed -> analyze -> draft -> redteam -> edit -> approve -> audit trail & queue.
Also verifies determinism of decision engine.
"""

import pytest
from app.main import app
from app.storage.db import init_db
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    # Initialize database
    init_db()
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["llm_status"] in ("ok", "unavailable")


def test_seed_and_lifecycle_end_to_end(client: TestClient):
    # 1. Seed database
    seed_resp = client.post("/seed")
    assert seed_resp.status_code == 200
    seed_data = seed_resp.json()
    assert seed_data["cases_created"] > 0

    # 2. List cases
    list_resp = client.get("/cases")
    assert list_resp.status_code == 200
    cases = list_resp.json()["cases"]
    assert len(cases) > 0

    target_case_id = cases[0]["id"]

    # 3. Analyze case
    analyze_resp = client.post(f"/cases/{target_case_id}/analyze")
    assert analyze_resp.status_code == 200
    case_analyzed = analyze_resp.json()
    assert case_analyzed["status"] == "analyzed"
    assert len(case_analyzed["facts"]) > 0
    assert case_analyzed["decision"] is not None
    assert case_analyzed["decision"]["recommendation"] in ["accept", "challenge", "escalate"]

    # 4. Draft response
    draft_resp = client.post(f"/cases/{target_case_id}/draft")
    assert draft_resp.status_code == 200
    case_drafted = draft_resp.json()
    assert case_drafted["status"] == "drafted"
    assert len(case_drafted["draft"]) > 0
    assert case_drafted["grounding_report"] is not None
    assert len(case_drafted["grounding_report"]["kept"]) == len(case_drafted["draft"])

    # 5. Red-Team review
    redteam_resp = client.post(f"/cases/{target_case_id}/redteam")
    assert redteam_resp.status_code == 200
    case_redteamed = redteam_resp.json()
    assert len(case_redteamed["redteam_findings"]) > 0

    # 6. Human edits draft
    original_sentence = case_drafted["draft"][0]
    edit_payload = {
        "draft": [original_sentence]
    }
    edit_resp = client.put(f"/cases/{target_case_id}/draft", json=edit_payload)
    assert edit_resp.status_code == 200
    case_edited = edit_resp.json()
    assert len(case_edited["draft"]) == 1

    # 7. Approve requires explicit confirmation
    unconfirmed_resp = client.post(
        f"/cases/{target_case_id}/approve",
        json={"approved_by": "Senior Analyst", "confirm": False},
    )
    assert unconfirmed_resp.status_code == 400
    assert "Explicit confirmation required" in unconfirmed_resp.json()["detail"]

    # Valid approval
    approve_resp = client.post(
        f"/cases/{target_case_id}/approve",
        json={"approved_by": "Senior Analyst", "confirm": True},
    )
    assert approve_resp.status_code == 200
    case_approved = approve_resp.json()
    assert case_approved["status"] == "approved"
    assert case_approved["approved_by"] == "Senior Analyst"
    assert case_approved["approved_at"] is not None

    # 8. Check audit trail
    audit_resp = client.get(f"/cases/{target_case_id}/audit")
    assert audit_resp.status_code == 200
    events = audit_resp.json()
    actions = [e["action"] for e in events]
    assert "created" in actions
    assert "analyzed" in actions
    assert "drafted" in actions
    assert "redteamed" in actions
    assert "edited" in actions
    assert "approved" in actions

    # 9. Triage queue
    queue_resp = client.get("/queue")
    assert queue_resp.status_code == 200
    queue_items = queue_resp.json()
    assert isinstance(queue_items, list)


def test_determinism(client: TestClient):
    """Verify that analyzing the exact same case twice produces identical decisions."""
    # Analyze CASE-0001 twice
    resp1 = client.post("/cases/CASE-0001/analyze")
    assert resp1.status_code == 200
    dec1 = resp1.json()["decision"]

    resp2 = client.post("/cases/CASE-0001/analyze")
    assert resp2.status_code == 200
    dec2 = resp2.json()["decision"]

    assert dec1["recommendation"] == dec2["recommendation"]
    assert dec1["evidence_strength"] == dec2["evidence_strength"]
    assert dec1["p_win_estimate"] == dec2["p_win_estimate"]
    assert dec1["economics"]["net_ev"] == dec2["economics"]["net_ev"]
