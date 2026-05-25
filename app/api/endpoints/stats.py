"""
Aggregate stats endpoint — counts across posts and opportunities.
Returns a single payload with everything the StatsBar needs.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.db.store import Store

router = APIRouter(prefix="/stats", tags=["stats"])
logger = logging.getLogger(__name__)


def _fetch_stats(db_path: str) -> dict:
    store = Store(db_path)
    try:
        # --- Post counts ---
        # All-time by status
        post_rows = store._fetchall(
            "SELECT status, COUNT(*) AS n FROM posts GROUP BY status"
        )
        posts_by_status: dict[str, int] = {r["status"]: r["n"] for r in post_rows}

        # Past 7 days total (any status)
        posts_7d = store._fetchone(
            "SELECT COUNT(*) AS n FROM posts WHERE posted_at >= datetime('now', '-7 days')"
        )

        # Top 5 communities by successful post count
        top_communities = store._fetchall(
            """
            SELECT target, COUNT(*) AS n
              FROM posts
             WHERE status = 'success'
             GROUP BY target
             ORDER BY n DESC
             LIMIT 5
            """
        )

        # Platform breakdown (success only)
        platform_rows = store._fetchall(
            "SELECT platform, COUNT(*) AS n FROM posts WHERE status = 'success' GROUP BY platform"
        )

        # --- Opportunity counts ---
        opp_rows = store._fetchall(
            "SELECT status, COUNT(*) AS n FROM opportunities GROUP BY status"
        )
        opps_by_status: dict[str, int] = {r["status"]: r["n"] for r in opp_rows}

        return {
            "posts": {
                "total": sum(posts_by_status.values()),
                "success": posts_by_status.get("success", 0),
                "failed": posts_by_status.get("failed", 0),
                "skipped": posts_by_status.get("skipped", 0),
                "last_7_days": (posts_7d or {}).get("n", 0),
                "by_platform": {r["platform"]: r["n"] for r in platform_rows},
                "top_communities": [
                    {"community": r["target"], "count": r["n"]} for r in top_communities
                ],
            },
            "opportunities": {
                "total": sum(opps_by_status.values()),
                "pending_review": opps_by_status.get("pending_review", 0),
                "approved": opps_by_status.get("approved", 0),
                "posted": opps_by_status.get("posted", 0),
                "manual_posted": opps_by_status.get("manual_posted", 0),
                "dismissed": opps_by_status.get("dismissed", 0),
            },
        }
    finally:
        store.close()


@router.get("")
async def get_stats() -> dict:
    """Aggregate stats across posts and opportunities."""
    db_path = get_settings().db_path
    logger.debug("Fetching aggregate stats")
    return await asyncio.to_thread(_fetch_stats, db_path)
