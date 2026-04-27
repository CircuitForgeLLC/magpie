from __future__ import annotations

import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.store import Store

router = APIRouter(prefix="/opportunities", tags=["opportunities"])

VALID_STATUSES = {"pending_review", "approved", "posted", "manual_posted", "dismissed"}


def _get_store() -> Store:
    return Store(get_settings().db_path)


def _in_thread(fn):
    store = _get_store()
    try:
        return fn(store)
    finally:
        store.close()


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class OpportunityCreate(BaseModel):
    platform: str = "reddit"
    community: str
    thread_url: str
    thread_title: str | None = None
    thread_body: str | None = None
    signal_reason: str | None = None
    product: str | None = None
    draft_title: str | None = None
    draft_body: str = ""
    post_type: Literal["reply_to_thread", "new_post"] = "reply_to_thread"
    campaign_id: int | None = None


class OpportunityUpdate(BaseModel):
    draft_title: str | None = None
    draft_body: str | None = None
    signal_reason: str | None = None
    product: str | None = None
    status: str | None = None
    campaign_id: int | None = None


class DismissBody(BaseModel):
    note: str | None = None


class MarkPostedBody(BaseModel):
    url: str | None = None


# ------------------------------------------------------------------ #
# Routes
# ------------------------------------------------------------------ #

@router.get("")
async def list_opportunities(status: str | None = None):
    if status and status not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Valid: {sorted(VALID_STATUSES)}")
    return await asyncio.to_thread(_in_thread, lambda s: s.list_opportunities(status))


@router.post("", status_code=201)
async def create_opportunity(body: OpportunityCreate):
    return await asyncio.to_thread(
        _in_thread,
        lambda s: s.create_opportunity(**body.model_dump()),
    )


@router.get("/{opportunity_id}")
async def get_opportunity(opportunity_id: int):
    result = await asyncio.to_thread(_in_thread, lambda s: s.get_opportunity(opportunity_id))
    if result is None:
        raise HTTPException(404, "Opportunity not found")
    return result


@router.patch("/{opportunity_id}")
async def update_opportunity(opportunity_id: int, body: OpportunityUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "status" in updates and updates["status"] not in VALID_STATUSES:
        raise HTTPException(400, f"Invalid status. Valid: {sorted(VALID_STATUSES)}")
    result = await asyncio.to_thread(
        _in_thread, lambda s: s.update_opportunity(opportunity_id, **updates)
    )
    if result is None:
        raise HTTPException(404, "Opportunity not found")
    return result


@router.post("/{opportunity_id}/approve")
async def approve_opportunity(opportunity_id: int):
    """Mark as approved. For Reddit opportunities, returns auto-post instructions.
    For other platforms, returns a manual handoff payload."""
    opp = await asyncio.to_thread(_in_thread, lambda s: s.get_opportunity(opportunity_id))
    if opp is None:
        raise HTTPException(404, "Opportunity not found")

    updated = await asyncio.to_thread(
        _in_thread, lambda s: s.approve_opportunity(opportunity_id)
    )

    if opp["platform"] == "reddit":
        return {
            "type": "auto_post_ready",
            "opportunity": updated,
            "instructions": "Use trigger_sub_post with the linked campaign, or fire manually via post.py.",
        }

    return {
        "type": "manual_handoff",
        "opportunity": updated,
        "draft_body": opp["draft_body"],
        "thread_url": opp["thread_url"],
        "instructions": (
            f"Copy the draft and reply to this thread manually ({opp['platform']}). "
            "Mark as manual_posted when done."
        ),
    }


@router.post("/{opportunity_id}/mark-posted")
async def mark_posted(opportunity_id: int, body: MarkPostedBody = MarkPostedBody(), manual: bool = False):
    """Record that a post was successfully made (auto or manual).
    When manual=True, also writes a row to the posts table for history tracking."""
    opp = await asyncio.to_thread(_in_thread, lambda s: s.get_opportunity(opportunity_id))
    if opp is None:
        raise HTTPException(404, "Opportunity not found")

    status = "manual_posted" if manual else "posted"
    result = await asyncio.to_thread(
        _in_thread, lambda s: s.update_opportunity(opportunity_id, status=status)
    )

    if manual:
        await asyncio.to_thread(
            _in_thread,
            lambda s: s.log_manual_post(
                opportunity_id=opportunity_id,
                platform=opp["platform"],
                target=opp["community"],
                url=body.url,
            ),
        )

    return result


@router.post("/{opportunity_id}/dismiss")
async def dismiss_opportunity(opportunity_id: int, body: DismissBody):
    result = await asyncio.to_thread(
        _in_thread, lambda s: s.dismiss_opportunity(opportunity_id, body.note)
    )
    if result is None:
        raise HTTPException(404, "Opportunity not found")
    return result
