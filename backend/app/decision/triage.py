"""
Triage Queue — deadline-aware dispute ranking.

score = (max(net_ev, 0) / effort_hours) * urgency

Urgency:
  > 72h left:  1.0
  24-72h left: 1.5
  < 24h left:  2.0

Overdue cases are pinned to the top with a warning.
Escalate cases rank by amount * urgency.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.config import get_config
from app.contracts import (
    Decision,
    DisputeCase,
    QueueItem,
    Recommendation,
)
from app.pii import safe_log

logger = logging.getLogger(__name__)


def compute_hours_left(deadline: str) -> float:
    """Calculate hours remaining until deadline."""
    try:
        deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        if deadline_dt.tzinfo is None:
            deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = deadline_dt - now
        return max(0.0, round(delta.total_seconds() / 3600, 1))
    except (ValueError, TypeError):
        return 72.0  # default if unparseable


def compute_urgency(hours_left: float) -> float:
    """Map hours left to urgency multiplier."""
    cfg = get_config()
    if hours_left < 24:
        return cfg.triage.urgency_high
    elif hours_left < 72:
        return cfg.triage.urgency_medium
    else:
        return cfg.triage.urgency_low


def compute_triage_score(
    case: DisputeCase,
    decision: Decision | None = None,
) -> QueueItem:
    """
    Compute triage score for a case.

    score = (max(net_ev, 0) / effort_hours) * urgency
    Escalate cases: amount * urgency
    Overdue cases: pinned to top
    """
    cfg = get_config()
    hours_left = compute_hours_left(case.deadline)
    urgency = compute_urgency(hours_left)
    is_overdue = hours_left <= 0

    if decision:
        net_ev = decision.economics.net_ev
        recommendation = decision.recommendation
    else:
        net_ev = 0.0
        recommendation = None

    # Compute score
    if is_overdue:
        # Overdue cases get a very high score to pin to top
        score = 1_000_000 + case.amount * urgency
    elif recommendation == Recommendation.ESCALATE:
        # Escalate: rank by amount * urgency
        score = case.amount * urgency
    else:
        # Normal: (max(net_ev, 0) / effort_hours) * urgency
        score = (max(net_ev, 0) / cfg.triage.effort_hours) * urgency

    score_breakdown = {
        "net_ev": net_ev,
        "effort_hours": cfg.triage.effort_hours,
        "urgency": urgency,
        "hours_left": hours_left,
        "is_overdue": float(is_overdue),
        "amount": case.amount,
    }

    deadline_warning = None
    if is_overdue:
        deadline_warning = "⚠️ OVERDUE — deadline has passed"
    elif hours_left < cfg.economics.min_preparation_hours:
        deadline_warning = f"⚠️ Only {hours_left:.1f}h left — immediate action required"
    elif hours_left < 24:
        deadline_warning = f"⏰ {hours_left:.1f}h remaining — high urgency"

    return QueueItem(
        case_id=case.id,
        reason=case.reason,
        amount=case.amount,
        hours_left=hours_left,
        recommendation=recommendation,
        score=round(score, 2),
        score_breakdown=score_breakdown,
        is_overdue=is_overdue,
        deadline_warning=deadline_warning,
    )


def rank_queue(cases: list[DisputeCase]) -> list[QueueItem]:
    """
    Rank all cases into a triage queue.
    Returns items sorted by score descending (highest priority first).
    """
    items: list[QueueItem] = []
    for case in cases:
        item = compute_triage_score(case, case.decision)
        items.append(item)

    # Sort by score descending
    items.sort(key=lambda x: x.score, reverse=True)

    logger.info(safe_log(f"Triage queue: {len(items)} cases ranked"))
    return items
