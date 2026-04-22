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
from apscheduler.triggers.interval import IntervalTrigger

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


# ------------------------------------------------------------------ #
# Signal scraper job
# ------------------------------------------------------------------ #

_SCRAPER_JOB_ID = "signal_scraper"


async def _run_scraper_job() -> None:
    """APScheduler coroutine target: run one pass of signal scraping."""
    from app.services.scraper import scrape_signals  # deferred to avoid circular imports
    logger.info("Signal scraper job starting")
    try:
        summary = await scrape_signals()
        logger.info(
            "Signal scraper done: %d sub(s), %d post(s) seen, %d signal(s) found",
            summary["subs_scraped"], summary["posts_seen"], summary["signals_found"],
        )
    except Exception:
        logger.exception("Unhandled error in signal scraper job")


def start_scraper_job(interval_mins: int = 30) -> None:
    """
    Register (or replace) the signal scraper interval job.

    Call this at startup when scraper_enabled=True.
    """
    sched = get_scheduler()
    existing = sched.get_job(_SCRAPER_JOB_ID)
    if existing:
        existing.remove()

    sched.add_job(
        _run_scraper_job,
        trigger=IntervalTrigger(minutes=interval_mins, timezone="UTC"),
        id=_SCRAPER_JOB_ID,
        replace_existing=True,
        misfire_grace_time=600,
    )
    logger.info("Signal scraper scheduled every %d minute(s)", interval_mins)


def stop_scraper_job() -> None:
    """Remove the signal scraper job (e.g. when disabling via settings)."""
    sched = get_scheduler()
    existing = sched.get_job(_SCRAPER_JOB_ID)
    if existing:
        existing.remove()
        logger.info("Signal scraper job removed")
