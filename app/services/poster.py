"""
Posting service: orchestrates variant resolution, dupe guard, and post execution.
Called by the scheduler and by the manual-trigger API endpoint.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.db.store import Store
from app.services.platforms import get_client, SUPPORTED_PLATFORMS


def _run_post(db_path: str, campaign_id: int, sub: str, triggered_by: str = "scheduler") -> dict:
    """Execute a single post attempt (blocking, runs in a thread)."""
    store = Store(db_path)
    try:
        # Dupe guard: skip if already posted to this sub this week
        if store.already_posted_this_week(campaign_id, sub):
            return {"skipped": True, "reason": f"already posted to r/{sub} this week"}

        # Resolve the best variant for this sub
        variant = store.resolve_variant(campaign_id, sub)
        if variant is None:
            return {"skipped": True, "reason": "no variant found for campaign"}

        # Check sub rules
        rules = store.get_sub_rules(sub)
        if rules and rules.get("promo_allowed") == 0:
            return {"skipped": True, "reason": f"r/{sub} hard-bans promotion"}

        # Check platform support
        campaign = store.get_campaign(campaign_id)
        platform = campaign["platform"] if campaign else "reddit"
        if platform not in SUPPORTED_PLATFORMS:
            return {"skipped": True, "reason": f"platform '{platform}' not yet implemented"}

        # Create the pending post record
        post = store.create_post(
            campaign_id=campaign_id,
            target=sub,
            variant_id=variant["id"],
            platform=platform,
            triggered_by=triggered_by,
        )
        post_id = post["id"]

        # Execute
        try:
            client = get_client(platform)
            flair = variant.get("flair") or (rules.get("flair_to_use") if rules else None)
            url = client.post(
                sub=sub,
                title=variant["title"],
                body=variant["body"],
                flair=flair,
            )
            return store.update_post_status(post_id, "success", url=url)
        except Exception as exc:
            return store.update_post_status(post_id, "failed", error_msg=str(exc))
    finally:
        store.close()


async def post_campaign_to_sub(campaign_id: int, sub: str,
                                triggered_by: str = "scheduler") -> dict:
    """Async wrapper for API and scheduler use."""
    db_path = get_settings().db_path
    return await asyncio.to_thread(_run_post, db_path, campaign_id, sub, triggered_by)


async def run_campaign(campaign_id: int, triggered_by: str = "scheduler") -> list[dict]:
    """Post a campaign to all of its configured subs, sequentially."""
    db_path = get_settings().db_path
    store = Store(db_path)
    try:
        subs = store.list_campaign_subs(campaign_id)
        active_subs = [s["sub"] for s in subs if s.get("active", 1)]
    finally:
        store.close()

    results = []
    for sub in active_subs:
        result = await post_campaign_to_sub(campaign_id, sub, triggered_by)
        results.append(result)
    return results
