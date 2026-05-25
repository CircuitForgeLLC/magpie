"""
Posting service: orchestrates variant resolution, dupe guard, and post execution.
Called by the scheduler and by the manual-trigger API endpoint.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date
from pathlib import Path

from app.core.config import get_settings
from app.db.store import Store
from app.services.platforms import get_client
from app.services.platforms.reddit_comment import is_nth_weekday, parse_occurrence

logger = logging.getLogger(__name__)


def _run_post(db_path: str, campaign_id: int, target: str,
              triggered_by: str = "scheduler") -> dict:
    """Execute a single post attempt (blocking, runs in a thread)."""
    store = Store(db_path)
    try:
        campaign = store.get_campaign(campaign_id)
        if campaign is None:
            return {"skipped": True, "reason": f"campaign {campaign_id} not found"}

        campaign_type = campaign.get("type", "reddit_post")

        # Resolve strategy — skip if type is unknown
        try:
            strategy = get_client(campaign_type)
        except ValueError as exc:
            return {"skipped": True, "reason": str(exc)}

        # Fetch the campaign_subs row for this target (used for extra + occurrence)
        all_subs = store.list_campaign_subs(campaign_id)
        sub_row = next((s for s in all_subs if s["sub"] == target), {})

        # Occurrence check — skip if not the right week of the month
        occurrence_str = sub_row.get("occurrence")
        try:
            parsed = parse_occurrence(occurrence_str)
        except ValueError as exc:
            return {"skipped": True, "reason": f"invalid occurrence {occurrence_str!r}: {exc}"}
        if parsed is not None:
            weekday, n = parsed
            if not is_nth_weekday(date.today(), weekday, n):
                logger.info(
                    "Skipping %s / %s — not occurrence %s today",
                    campaign_id, target, occurrence_str,
                )
                return {"skipped": True, "reason": f"occurrence {occurrence_str} not today"}

        # Per-sub post cap (max_posts=None means unlimited)
        max_posts = sub_row.get("max_posts")
        if max_posts is not None:
            count = store.successful_post_count(campaign_id, target)
            if count >= max_posts:
                logger.info(
                    "Skipping %s / %s — reached max_posts=%d (posted %d time(s))",
                    campaign_id, target, max_posts, count,
                )
                return {"skipped": True, "reason": f"max_posts={max_posts} reached for {target!r}"}

        # Dupe guard (opt-out allowed per strategy)
        if strategy.supports_dupe_guard() and store.already_posted_this_week(campaign_id, target):
            return {"skipped": True, "reason": f"already posted to {target!r} this week"}

        # Resolve best content variant for this target
        variant = store.resolve_variant(campaign_id, target)
        if variant is None:
            return {"skipped": True, "reason": "no variant found for campaign"}

        # Check platform rules (Reddit-specific; harmless for other platforms)
        rules = store.get_sub_rules(target)
        if rules and rules.get("promo_allowed") == 0:
            return {"skipped": True, "reason": f"{target!r} hard-bans promotion"}

        # Create pending post record
        post = store.create_post(
            campaign_id=campaign_id,
            target=target,
            variant_id=variant["id"],
            platform=campaign.get("platform", "reddit"),
            triggered_by=triggered_by,
        )
        post_id = post["id"]

        # Build extra dict from sub_row; merge variant-level blog fields (blog_post strategy uses them)
        extra = dict(sub_row)
        for field in ("slug", "tags", "seo_description"):
            if variant.get(field) is not None:
                extra.setdefault(field, variant[field])

        # Execute strategy
        flair = variant.get("flair") or (rules.get("flair_to_use") if rules else None)
        try:
            result = strategy.execute(
                target=target,
                title=variant.get("title", ""),
                body=variant.get("body", ""),
                flair=flair,
                extra=extra,
            )
            return store.update_post_status(post_id, "success", url=result.url)
        except Exception as exc:
            logger.exception("Strategy %s failed for target %r", campaign_type, target)
            return store.update_post_status(post_id, "failed", error_msg=str(exc))
    finally:
        store.close()


async def post_campaign_to_sub(campaign_id: int, target: str,
                               triggered_by: str = "scheduler") -> dict:
    """Async wrapper for API and scheduler use."""
    db_path = get_settings().db_path
    return await asyncio.to_thread(_run_post, db_path, campaign_id, target, triggered_by)


async def run_campaign(campaign_id: int, triggered_by: str = "scheduler") -> list[dict]:
    """Post a campaign to all of its configured targets, sequentially."""
    db_path = get_settings().db_path
    store = Store(db_path)
    try:
        subs = store.list_campaign_subs(campaign_id)
        active_targets = [s["sub"] for s in subs if s.get("active", 1)]
    finally:
        store.close()

    results = []
    for target in active_targets:
        result = await post_campaign_to_sub(campaign_id, target, triggered_by)
        results.append(result)
    return results
