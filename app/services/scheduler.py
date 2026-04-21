"""
Campaign scheduler: wraps APScheduler's AsyncIOScheduler.

One cron job per active campaign with a cron_schedule.
Jobs are re-synced at startup and updated dynamically via sync_campaign().
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.poster import run_campaign

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Module-level singleton — attached to app.state in main.py so it is accessible
# from endpoints without importing it directly.
_scheduler: AsyncIOScheduler | None = None


def _job_id(campaign_id: int) -> str:
    return f"campaign_{campaign_id}"


async def _run_campaign_job(campaign_id: int) -> None:
    """APScheduler coroutine target: run a campaign and log the outcome."""
    logger.info("Scheduler firing campaign %d", campaign_id)
    try:
        results = await run_campaign(campaign_id, triggered_by="scheduler")
        success = sum(1 for r in results if not r.get("skipped") and r.get("status") == "success")
        skipped = sum(1 for r in results if r.get("skipped"))
        failed = sum(1 for r in results if not r.get("skipped") and r.get("status") == "failed")
        logger.info(
            "Campaign %d done: %d success, %d skipped, %d failed",
            campaign_id, success, skipped, failed,
        )
    except Exception:
        logger.exception("Unhandled error running campaign %d", campaign_id)


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="UTC")
    return _scheduler


def start_scheduler() -> AsyncIOScheduler:
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        logger.info("Scheduler started")
    return sched


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
    _scheduler = None


def sync_campaign(campaign: dict) -> None:
    """
    Add, update, or remove the cron job for a campaign.

    Call this after any create / update / delete / toggle.
    """
    sched = get_scheduler()
    job_id = _job_id(campaign["id"])
    cron_expr = campaign.get("cron_schedule")
    is_active = bool(campaign.get("active", 1))

    # Remove existing job (if any) before re-adding so schedule changes take effect
    existing = sched.get_job(job_id)
    if existing:
        existing.remove()

    if cron_expr and is_active:
        try:
            trigger = CronTrigger.from_crontab(cron_expr, timezone="UTC")
            sched.add_job(
                _run_campaign_job,
                trigger=trigger,
                id=job_id,
                args=[campaign["id"]],
                replace_existing=True,
                misfire_grace_time=3600,  # fire up to 1 hour late (e.g. after a restart)
            )
            logger.info(
                "Scheduled campaign %d (%s) with cron: %s",
                campaign["id"], campaign.get("name", ""), cron_expr,
            )
        except Exception:
            logger.exception(
                "Invalid cron expression for campaign %d: %r",
                campaign["id"], cron_expr,
            )


def remove_campaign(campaign_id: int) -> None:
    """Remove the cron job for a deleted campaign."""
    sched = get_scheduler()
    existing = sched.get_job(_job_id(campaign_id))
    if existing:
        existing.remove()
        logger.info("Removed scheduler job for campaign %d", campaign_id)


def sync_all_campaigns(campaigns: list[dict]) -> None:
    """Sync scheduler state from a full campaign list (called at startup)."""
    for campaign in campaigns:
        sync_campaign(campaign)
    logger.info("Synced %d campaign(s) to scheduler", len(campaigns))
