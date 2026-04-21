from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.store import Store

router = APIRouter(prefix="/subs", tags=["subs"])


def _in_thread(fn):
    store = Store(get_settings().db_path)
    try:
        return fn(store)
    finally:
        store.close()


class SubRulesUpsert(BaseModel):
    flair_required: bool = False
    flair_to_use: str | None = None
    promo_allowed: bool | None = None    # None = unknown
    rule_warning: bool = False
    notes: str | None = None


@router.get("")
async def list_sub_rules(platform: str = "reddit"):
    return await asyncio.to_thread(_in_thread, lambda s: s.list_sub_rules(platform))


@router.get("/{sub}")
async def get_sub_rules(sub: str, platform: str = "reddit"):
    result = await asyncio.to_thread(_in_thread, lambda s: s.get_sub_rules(sub, platform))
    if result is None:
        raise HTTPException(404, f"No rules on record for r/{sub}")
    return result


@router.put("/{sub}")
async def upsert_sub_rules(sub: str, body: SubRulesUpsert, platform: str = "reddit"):
    fields = body.model_dump()
    # Convert bool | None to int | None for SQLite
    if fields.get("promo_allowed") is not None:
        fields["promo_allowed"] = 1 if fields["promo_allowed"] else 0
    fields["flair_required"] = 1 if fields["flair_required"] else 0
    fields["rule_warning"] = 1 if fields["rule_warning"] else 0
    return await asyncio.to_thread(
        _in_thread, lambda s: s.upsert_sub_rules(sub, platform, **fields)
    )
