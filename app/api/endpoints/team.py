"""
Team accounts — list and manage posting identities across platforms.
Read operations are available to all; create/update reserved for admin use.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.db.store import Store

router = APIRouter(prefix="/team", tags=["team"])
logger = logging.getLogger(__name__)


def _get_store() -> Store:
    return Store(get_settings().db_path)


def _in_thread(fn):
    store = _get_store()
    try:
        return fn(store)
    finally:
        store.close()


class TeamAccountCreate(BaseModel):
    display_name: str
    platform: str
    username: str
    account_type: str = "personal"
    session_file: str | None = None
    notes: str | None = None


# ------------------------------------------------------------------ #
# Routes
# ------------------------------------------------------------------ #

@router.get("")
async def list_team_accounts(platform: str | None = None, active_only: bool = True):
    """List all registered team accounts. Filter by platform if provided."""
    return await asyncio.to_thread(
        _in_thread,
        lambda s: s.list_team_accounts(platform=platform, active_only=active_only),
    )


@router.get("/{account_id}")
async def get_team_account(account_id: int):
    result = await asyncio.to_thread(_in_thread, lambda s: s.get_team_account(account_id))
    if result is None:
        raise HTTPException(404, "Team account not found")
    return result


@router.post("", status_code=201)
async def create_team_account(body: TeamAccountCreate):
    logger.info(
        "Creating team account: %s / %s (%s)", body.display_name, body.platform, body.account_type
    )
    return await asyncio.to_thread(
        _in_thread,
        lambda s: s.create_team_account(**body.model_dump()),
    )


@router.post("/{opportunity_id}/assign")
async def assign_opportunity(
    opportunity_id: int,
    assigned_to: int | None = None,
    post_as: int | None = None,
):
    """Assign an opportunity to a team member and/or set the posting account."""
    result = await asyncio.to_thread(
        _in_thread,
        lambda s: s.assign_opportunity(opportunity_id, assigned_to, post_as),
    )
    if result is None:
        raise HTTPException(404, "Opportunity not found")
    logger.info(
        "Opportunity %s assigned_to=%s post_as=%s", opportunity_id, assigned_to, post_as
    )
    return result
