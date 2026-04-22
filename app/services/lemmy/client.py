"""
Lemmy API v3 client — read-only, no auth required for public communities.

Community addressing convention: <community>@<instance>
  e.g. "selfhosted@lemmy.world", "technology@reddthat.com"

API reference: https://{instance}/api/v3/
Key endpoints used:
  GET /api/v3/post/list?community_name=<name>&sort=New&limit=<n>&page=<p>
  GET /api/v3/community?name=<name>  (validation / metadata)
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Instances known to be reliably federated and publicly accessible
KNOWN_INSTANCES = frozenset([
    "lemmy.world",
    "lemmy.ml",
    "beehaw.org",
    "reddthat.com",
    "sh.itjust.works",
    "feddit.de",
    "aussie.zone",
    "lemmy.ca",
])

_DEFAULT_TIMEOUT = 15.0
_DEFAULT_USER_AGENT = "Magpie/0.1 signal-monitor (by CircuitForge)"


def parse_community_target(sub: str) -> tuple[str, str]:
    """
    Parse a 'community@instance' string into (community_name, instance_host).

    Raises ValueError if the format is invalid.
    """
    if "@" not in sub:
        raise ValueError(
            f"Lemmy community must be in 'community@instance' format, got: {sub!r}"
        )
    community, instance = sub.rsplit("@", 1)
    if not community or not instance:
        raise ValueError(f"Invalid Lemmy community target: {sub!r}")
    return community.strip(), instance.strip().lower()


async def fetch_new_posts(
    community: str,
    instance: str,
    last_seen_id: int | None,
    limit: int = 50,
    user_agent: str = _DEFAULT_USER_AGENT,
) -> tuple[list[dict[str, Any]], int | None]:
    """
    Fetch new posts from a Lemmy community.

    Fetches the first page sorted by New, then filters to posts with
    id > last_seen_id (client-side cursor — Lemmy has no 'before' param).

    Returns:
        posts       — filtered list of post dicts, newest first
        new_max_id  — highest post ID seen this run (use as next cursor), or None
    """
    url = f"https://{instance}/api/v3/post/list"
    params = {
        "community_name": community,
        "sort": "New",
        "limit": min(limit, 50),  # Lemmy max is 50 per page
        "type_": "Local",         # stay within the instance's local community
    }

    async with httpx.AsyncClient(
        headers={"User-Agent": user_agent},
        follow_redirects=True,
        timeout=_DEFAULT_TIMEOUT,
    ) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    post_views = data.get("posts", [])

    # Normalize to flat dicts and apply cursor filter
    posts = []
    new_max_id: int | None = None

    for pv in post_views:
        post = pv.get("post", {})
        counts = pv.get("counts", {})
        creator = pv.get("creator", {})

        post_id: int = post.get("id", 0)

        # Track max ID regardless of cursor (always advance)
        if new_max_id is None or post_id > new_max_id:
            new_max_id = post_id

        # Apply cursor: skip posts we've already seen
        if last_seen_id is not None and post_id <= last_seen_id:
            continue

        posts.append({
            "id": post_id,
            "ap_id": post.get("ap_id", f"https://{instance}/post/{post_id}"),
            "title": post.get("name", ""),
            "body": post.get("body", "") or "",
            "url": post.get("ap_id", ""),          # ap_id is the canonical URL
            "author": creator.get("name", ""),
            "score": counts.get("score", 0),
            "comment_count": counts.get("comments", 0),
            "published": post.get("published", ""),
            "community": community,
            "instance": instance,
        })

    return posts, new_max_id
