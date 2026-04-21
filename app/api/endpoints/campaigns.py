from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.store import Store
from app.services.poster import run_campaign
from app.services.scheduler import remove_campaign as scheduler_remove, sync_campaign

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


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

class CampaignCreate(BaseModel):
    name: str
    product: str
    platform: str = "reddit"
    cron_schedule: str | None = None
    notes: str | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    product: str | None = None
    cron_schedule: str | None = None
    active: bool | None = None
    notes: str | None = None


class VariantCreate(BaseModel):
    sub_pattern: str = "*"
    title: str
    body: str
    flair: str | None = None
    notes: str | None = None


class VariantUpdate(BaseModel):
    sub_pattern: str | None = None
    title: str | None = None
    body: str | None = None
    flair: str | None = None
    notes: str | None = None


class SubEntry(BaseModel):
    sub: str
    sort_order: int = 0


# ------------------------------------------------------------------ #
# Campaign CRUD
# ------------------------------------------------------------------ #

@router.get("")
async def list_campaigns(active_only: bool = False):
    return await asyncio.to_thread(_in_thread, lambda s: s.list_campaigns(active_only))


@router.post("", status_code=201)
async def create_campaign(body: CampaignCreate):
    campaign = await asyncio.to_thread(
        _in_thread,
        lambda s: s.create_campaign(**body.model_dump()),
    )
    sync_campaign(campaign)
    return campaign


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: int):
    result = await asyncio.to_thread(_in_thread, lambda s: s.get_campaign(campaign_id))
    if result is None:
        raise HTTPException(404, "Campaign not found")
    return result


@router.patch("/{campaign_id}")
async def update_campaign(campaign_id: int, body: CampaignUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "active" in updates:
        updates["active"] = 1 if updates["active"] else 0
    result = await asyncio.to_thread(_in_thread, lambda s: s.update_campaign(campaign_id, **updates))
    if result is None:
        raise HTTPException(404, "Campaign not found")
    sync_campaign(result)
    return result


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: int):
    ok = await asyncio.to_thread(_in_thread, lambda s: s.delete_campaign(campaign_id))
    if not ok:
        raise HTTPException(404, "Campaign not found")
    scheduler_remove(campaign_id)


# ------------------------------------------------------------------ #
# Manual trigger
# ------------------------------------------------------------------ #

@router.post("/{campaign_id}/trigger")
async def trigger_campaign(campaign_id: int):
    """Manually fire a campaign to all its configured subs."""
    campaign = await asyncio.to_thread(_in_thread, lambda s: s.get_campaign(campaign_id))
    if campaign is None:
        raise HTTPException(404, "Campaign not found")
    results = await run_campaign(campaign_id, triggered_by="manual")
    return {"campaign_id": campaign_id, "results": results}


# ------------------------------------------------------------------ #
# Variants
# ------------------------------------------------------------------ #

@router.get("/{campaign_id}/variants")
async def list_variants(campaign_id: int):
    return await asyncio.to_thread(_in_thread, lambda s: s.list_variants(campaign_id))


@router.post("/{campaign_id}/variants", status_code=201)
async def create_variant(campaign_id: int, body: VariantCreate):
    return await asyncio.to_thread(
        _in_thread,
        lambda s: s.create_variant(campaign_id=campaign_id, **body.model_dump()),
    )


@router.patch("/{campaign_id}/variants/{variant_id}")
async def update_variant(campaign_id: int, variant_id: int, body: VariantUpdate):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    result = await asyncio.to_thread(_in_thread, lambda s: s.update_variant(variant_id, **updates))
    if result is None:
        raise HTTPException(404, "Variant not found")
    return result


@router.delete("/{campaign_id}/variants/{variant_id}", status_code=204)
async def delete_variant(campaign_id: int, variant_id: int):
    ok = await asyncio.to_thread(_in_thread, lambda s: s.delete_variant(variant_id))
    if not ok:
        raise HTTPException(404, "Variant not found")


# ------------------------------------------------------------------ #
# Subs
# ------------------------------------------------------------------ #

@router.get("/{campaign_id}/subs")
async def list_campaign_subs(campaign_id: int):
    return await asyncio.to_thread(_in_thread, lambda s: s.list_campaign_subs(campaign_id))


@router.post("/{campaign_id}/subs", status_code=201)
async def add_campaign_sub(campaign_id: int, body: SubEntry):
    return await asyncio.to_thread(
        _in_thread,
        lambda s: s.add_campaign_sub(campaign_id, body.sub, body.sort_order),
    )


@router.delete("/{campaign_id}/subs/{sub}", status_code=204)
async def remove_campaign_sub(campaign_id: int, sub: str):
    ok = await asyncio.to_thread(_in_thread, lambda s: s.remove_campaign_sub(campaign_id, sub))
    if not ok:
        raise HTTPException(404, "Sub not found in campaign")
