from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.db.store import Store

router = APIRouter()


def get_store() -> Store:
    s = get_settings()
    return Store(s.db_path)


# ------------------------------------------------------------------ #
# Schemas
# ------------------------------------------------------------------ #

class SignalRuleCreate(BaseModel):
    name: str
    platform: str = "reddit"
    sub: str | None = None
    keywords: list[str] = Field(default_factory=list)
    match_mode: str = "any"      # any | all | regex
    min_score: int = 0
    label: str | None = None     # pain-point | feedback | mention | trust
    notes: str | None = None


class SignalRuleUpdate(BaseModel):
    name: str | None = None
    sub: str | None = None
    keywords: list[str] | None = None
    match_mode: str | None = None
    min_score: int | None = None
    label: str | None = None
    active: bool | None = None
    notes: str | None = None


class SignalStatusUpdate(BaseModel):
    status: str           # new | saved | dismissed
    notes: str | None = None


def _decode_json_fields(row: dict[str, Any]) -> dict[str, Any]:
    """Decode JSON-encoded list fields returned as strings from SQLite."""
    for col in ("keywords", "matched_keywords"):
        if col in row and isinstance(row[col], str):
            try:
                row[col] = json.loads(row[col])
            except (json.JSONDecodeError, TypeError):
                row[col] = []
    return row


# ------------------------------------------------------------------ #
# Signal rules
# ------------------------------------------------------------------ #

@router.get("/signal-rules")
def list_signal_rules(active_only: bool = False, store: Store = Depends(get_store)):
    return [_decode_json_fields(r) for r in store.list_signal_rules(active_only=active_only)]


@router.post("/signal-rules", status_code=201)
def create_signal_rule(body: SignalRuleCreate, store: Store = Depends(get_store)):
    rule = store.create_signal_rule(
        name=body.name,
        platform=body.platform,
        sub=body.sub,
        keywords=body.keywords,
        match_mode=body.match_mode,
        min_score=body.min_score,
        label=body.label,
        notes=body.notes,
    )
    return _decode_json_fields(rule)


@router.get("/signal-rules/{rule_id}")
def get_signal_rule(rule_id: int, store: Store = Depends(get_store)):
    rule = store.get_signal_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Signal rule not found")
    return _decode_json_fields(rule)


@router.patch("/signal-rules/{rule_id}")
def update_signal_rule(rule_id: int, body: SignalRuleUpdate, store: Store = Depends(get_store)):
    rule = store.get_signal_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Signal rule not found")
    updates = body.model_dump(exclude_none=True)
    updated = store.update_signal_rule(rule_id, **updates)
    return _decode_json_fields(updated)


@router.delete("/signal-rules/{rule_id}", status_code=204)
def delete_signal_rule(rule_id: int, store: Store = Depends(get_store)):
    if not store.delete_signal_rule(rule_id):
        raise HTTPException(status_code=404, detail="Signal rule not found")


# ------------------------------------------------------------------ #
# Signals queue — fixed-path routes MUST precede /{signal_id} routes
# (FastAPI matches in registration order; literal paths win over params)
# ------------------------------------------------------------------ #

@router.get("/signals")
def list_signals(
    status: str | None = None,
    platform: str | None = None,
    sub: str | None = None,
    limit: int = 100,
    store: Store = Depends(get_store),
):
    rows = store.list_signals(status=status, platform=platform, sub=sub, limit=limit)
    return [_decode_json_fields(r) for r in rows]


@router.post("/signals/scrape")
async def trigger_scrape():
    """Manually trigger a full signal scrape pass. Useful for testing rules."""
    from app.services.scraper import scrape_signals
    summary = await scrape_signals()
    return summary


@router.get("/signals/scrape-state")
def get_scrape_state(store: Store = Depends(get_store)):
    """Return per-sub cursor state (last scraped, posts seen, signals found)."""
    return store.list_scrape_states()


@router.get("/signals/{signal_id}")
def get_signal(signal_id: int, store: Store = Depends(get_store)):
    signal = store.get_signal(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    result = _decode_json_fields(signal)
    result["matched_rules"] = store.get_signal_rule_matches(signal_id)
    return result


@router.patch("/signals/{signal_id}/status")
def update_signal_status(signal_id: int, body: SignalStatusUpdate, store: Store = Depends(get_store)):
    allowed = {"new", "saved", "dismissed"}
    if body.status not in allowed:
        raise HTTPException(status_code=422, detail=f"status must be one of {allowed}")
    signal = store.update_signal_status(signal_id, body.status, body.notes)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return _decode_json_fields(signal)
