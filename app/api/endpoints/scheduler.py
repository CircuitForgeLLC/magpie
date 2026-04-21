"""Scheduler status endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.services.scheduler import get_scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/status")
async def scheduler_status():
    """Return running state and next-fire-time for all scheduled jobs."""
    sched = get_scheduler()
    jobs = []
    for job in sched.get_jobs():
        jobs.append({
            "job_id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    return {"running": sched.running, "jobs": jobs}
