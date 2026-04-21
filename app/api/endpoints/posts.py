from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.store import Store
from app.services.poster import post_campaign_to_sub

router = APIRouter(prefix="/posts", tags=["posts"])


def _in_thread(fn):
    store = Store(get_settings().db_path)
    try:
        return fn(store)
    finally:
        store.close()


class PostToSub(BaseModel):
    campaign_id: int
    sub: str


@router.get("")
async def list_posts(campaign_id: int | None = None, target: str | None = None, limit: int = 50):
    return await asyncio.to_thread(
        _in_thread, lambda s: s.list_posts(campaign_id, target, limit)
    )


@router.post("/trigger")
async def trigger_single_post(body: PostToSub):
    """Manually trigger a single post to one sub."""
    campaign = await asyncio.to_thread(_in_thread, lambda s: s.get_campaign(body.campaign_id))
    if campaign is None:
        raise HTTPException(404, "Campaign not found")
    return await post_campaign_to_sub(body.campaign_id, body.sub, triggered_by="manual")


@router.get("/{post_id}/engagement")
async def get_engagement(post_id: int):
    result = await asyncio.to_thread(_in_thread, lambda s: s.get_latest_engagement(post_id))
    if result is None:
        raise HTTPException(404, "No engagement data for this post")
    return result
