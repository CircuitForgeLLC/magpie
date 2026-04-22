"""
Signal scraper: polls Reddit and Lemmy for posts matching signal_rules.

Architecture:
  - One global APScheduler interval job dispatches to per-platform fetchers.
  - Reddit: public JSON API, cursor via fullname (t3_xxxxx) + `before` param.
  - Lemmy: public v3 API, cursor via max integer post ID (client-side filter).
  - Correctness dedup lives in the DB (UNIQUE platform+post_id + INSERT OR IGNORE).
    Cursors are a performance optimization, not a correctness mechanism.
  - Keyword matching (_matches_rule) is platform-agnostic — all rules evaluated
    in one pass per fetched post to avoid redundant work.

Adding a new platform:
  1. Add a fetch function returning (posts: list[NormalizedPost], cursor: str | None).
  2. Add a branch in _process_platform_sub().
  3. Add the platform string to signal_rules rows.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.db.store import Store

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Reddit fetch
# ------------------------------------------------------------------ #

async def _fetch_reddit_posts(
    sub: str,
    before: str | None,
    limit: int,
    user_agent: str,
) -> tuple[list[dict[str, Any]], str | None]:
    """
    Fetch new posts from r/{sub}.

    Returns:
        posts      — list of raw post data dicts (newest first)
        new_cursor — fullname of the newest post fetched, or None if empty
    """
    params: dict[str, Any] = {"limit": limit, "raw_json": 1}
    if before:
        # 'before' in Reddit listing API = posts ABOVE this fullname = newer posts
        params["before"] = before

    url = f"https://www.reddit.com/r/{sub}/new.json"

    async with httpx.AsyncClient(
        headers={"User-Agent": user_agent},
        follow_redirects=True,
        timeout=15.0,
    ) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    children = data.get("data", {}).get("children", [])
    posts = [c["data"] for c in children if c.get("kind") == "t3"]

    # Newest post is first in the list; its fullname becomes the next cursor
    new_cursor = posts[0]["name"] if posts else None

    return posts, new_cursor


# ------------------------------------------------------------------ #
# Keyword matching
# ------------------------------------------------------------------ #

def _matches_rule(post: dict[str, Any], rule: dict[str, Any]) -> list[str]:
    """
    Check if a post matches a signal rule.

    Returns a list of matched keywords (non-empty = match), or [] (no match).
    """
    haystack = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
    keywords: list[str] = json.loads(rule["keywords"]) if isinstance(rule["keywords"], str) else rule["keywords"]
    match_mode: str = rule.get("match_mode", "any")
    min_score: int = rule.get("min_score", 0)

    # Score gate: skip posts below the minimum
    post_score = post.get("score", 0) or 0
    if post_score < min_score:
        return []

    # No keywords = match everything (useful for "watch this sub broadly")
    if not keywords:
        return ["*"]

    if match_mode == "regex":
        matched = []
        for pattern in keywords:
            try:
                if re.search(pattern, haystack, re.IGNORECASE):
                    matched.append(pattern)
            except re.error:
                logger.warning("Invalid regex in rule %d: %r", rule["id"], pattern)
        return matched if matched else []

    if match_mode == "all":
        matched = [kw for kw in keywords if kw.lower() in haystack]
        return matched if len(matched) == len(keywords) else []

    # Default: any
    return [kw for kw in keywords if kw.lower() in haystack]


# ------------------------------------------------------------------ #
# Normalized post type
# ------------------------------------------------------------------ #

# Both platform fetchers normalize their output to this shape before
# the common matching + upsert pipeline runs.
#
# Fields mirror Reddit's naming where possible so _matches_rule() which
# uses "title" and "selftext" works without platform-specific branches.
class NormalizedPost(dict):
    """
    Keys guaranteed present:
      post_id      str   — unique within platform (Reddit fullname, Lemmy ap_id URL)
      title        str
      selftext     str   — body text (empty string if none)
      score        int
      num_comments int
      author       str
      url          str
      created_utc  float | None
    """


def _normalize_reddit(post: dict[str, Any]) -> NormalizedPost:
    return NormalizedPost({
        "post_id": post["name"],
        "title": post.get("title", ""),
        "selftext": post.get("selftext", "") or "",
        "score": post.get("score", 0),
        "num_comments": post.get("num_comments", 0),
        "author": post.get("author", ""),
        "url": post.get("url", ""),
        "created_utc": post.get("created_utc"),
    })


def _normalize_lemmy(post: dict[str, Any]) -> NormalizedPost:
    published = post.get("published", "")
    try:
        ts = datetime.fromisoformat(published.rstrip("Z")).replace(tzinfo=timezone.utc).timestamp()
    except (ValueError, AttributeError):
        ts = None
    return NormalizedPost({
        "post_id": post["ap_id"],
        "title": post.get("title", ""),
        "selftext": post.get("body", "") or "",
        "score": post.get("score", 0),
        "num_comments": post.get("comment_count", 0),
        "author": post.get("author", ""),
        "url": post.get("url", "") or post.get("ap_id", ""),
        "created_utc": ts,
    })


# ------------------------------------------------------------------ #
# Common match + upsert pipeline
# ------------------------------------------------------------------ #

def _run_matching(
    post: NormalizedPost,
    rules: list[dict],
) -> tuple[list[int], list[str]]:
    """Apply all rules to a post. Returns (matched_rule_ids, matched_keywords)."""
    matched_kws: set[str] = set()
    matched_rule_ids: list[int] = []
    for rule in rules:
        kws = _matches_rule(post, rule)
        if kws:
            matched_kws.update(k for k in kws if k != "*")
            matched_rule_ids.append(rule["id"])
    return matched_rule_ids, sorted(matched_kws)


def _upsert_post(
    post: NormalizedPost,
    platform: str,
    sub: str,
    matched_rule_ids: list[int],
    matched_kws: list[str],
    store: Store,
) -> None:
    posted_at = (
        datetime.fromtimestamp(post["created_utc"], tz=timezone.utc).isoformat()
        if post.get("created_utc")
        else None
    )
    signal = store.upsert_signal(
        platform=platform,
        sub=sub,
        post_id=post["post_id"],
        title=post["title"],
        body_snippet=(post["selftext"][:500] or None),
        score=post["score"],
        comment_count=post["num_comments"],
        author=post["author"],
        url=post["url"],
        posted_at=posted_at,
        matched_keywords=matched_kws,
    )
    for rule_id in matched_rule_ids:
        store.record_signal_rule_match(signal["id"], rule_id)


# ------------------------------------------------------------------ #
# Core scraper
# ------------------------------------------------------------------ #

def _build_target_map(
    all_rules: list[dict],
) -> dict[tuple[str, str], list[dict]]:
    """
    Build a (platform, sub) → [rules] map from active rules.

    Rules with sub=None are global and appended to every explicit target.
    Returns an empty dict if no sub-specific targets exist.
    """
    global_rules_by_platform: dict[str, list[dict]] = {}
    target_map: dict[tuple[str, str], list[dict]] = {}

    for rule in all_rules:
        platform = rule.get("platform", "reddit")
        if not rule["sub"]:
            global_rules_by_platform.setdefault(platform, []).append(rule)
        else:
            key = (platform, rule["sub"])
            target_map.setdefault(key, []).append(rule)

    # Attach global rules to each explicit target of the same platform
    for (platform, _sub), rules in target_map.items():
        rules.extend(global_rules_by_platform.get(platform, []))

    return target_map


async def scrape_signals() -> dict[str, int]:
    """
    Run one full scrape pass across all platforms and monitored communities.

    Returns: {"subs_scraped": N, "posts_seen": N, "signals_found": N}
    """
    from app.services.lemmy.client import fetch_new_posts as lemmy_fetch, parse_community_target

    settings = get_settings()
    store = Store(settings.db_path)

    try:
        all_rules = store.list_signal_rules(active_only=True)
        if not all_rules:
            logger.info("Signal scraper: no active rules, skipping")
            return {"subs_scraped": 0, "posts_seen": 0, "signals_found": 0}

        target_map = _build_target_map(all_rules)
        if not target_map:
            logger.info("Signal scraper: global rules but no sub targets — add sub-specific rules")
            return {"subs_scraped": 0, "posts_seen": 0, "signals_found": 0}

        total_posts = 0
        total_signals = 0

        for (platform, sub), rules in target_map.items():
            state = store.get_scrape_state(sub, platform)
            cursor = state["last_fullname"] if state else None
            label = f"{platform}:{sub}"

            logger.info("Scraping %s (cursor=%s, rules=%d)", label, cursor, len(rules))

            # ---- Fetch -----------------------------------------------
            raw_posts: list[dict[str, Any]] = []
            new_cursor: str | None = None

            try:
                if platform == "reddit":
                    raw_posts, new_cursor = await _fetch_reddit_posts(
                        sub=sub,
                        before=cursor,
                        limit=settings.scraper_fetch_limit,
                        user_agent=settings.scraper_user_agent,
                    )
                    normalize = _normalize_reddit

                elif platform == "lemmy":
                    community, instance = parse_community_target(sub)
                    last_id = int(cursor) if cursor and cursor.isdigit() else None
                    lemmy_posts, max_id = await lemmy_fetch(
                        community=community,
                        instance=instance,
                        last_seen_id=last_id,
                        limit=settings.scraper_fetch_limit,
                        user_agent=settings.scraper_user_agent,
                    )
                    raw_posts = lemmy_posts
                    new_cursor = str(max_id) if max_id is not None else None
                    normalize = _normalize_lemmy

                else:
                    logger.warning("Unknown platform %r for sub %r — skipping", platform, sub)
                    continue

            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (403, 404):
                    logger.warning("%s returned %d — community may be private", label, exc.response.status_code)
                else:
                    logger.error("HTTP error scraping %s: %s", label, exc)
                await asyncio.sleep(settings.scraper_request_delay_secs)
                continue
            except ValueError as exc:
                logger.error("Config error for %s: %s", label, exc)
                continue
            except Exception:
                logger.exception("Unexpected error scraping %s", label)
                await asyncio.sleep(settings.scraper_request_delay_secs)
                continue

            # ---- Match + upsert --------------------------------------
            sub_signals = 0
            for raw in raw_posts:
                total_posts += 1
                post = normalize(raw)
                matched_rule_ids, matched_kws = _run_matching(post, rules)
                if not matched_rule_ids:
                    continue
                _upsert_post(post, platform, sub, matched_rule_ids, matched_kws, store)
                sub_signals += 1
                logger.debug("Signal: %s — %s", label, post["title"][:60])

            total_signals += sub_signals

            if new_cursor:
                store.update_scrape_state(
                    sub=sub,
                    platform=platform,
                    last_fullname=new_cursor,
                    posts_seen_delta=len(raw_posts),
                    signals_found_delta=sub_signals,
                )

            logger.info("%s: %d posts checked, %d signal(s) found", label, len(raw_posts), sub_signals)
            await asyncio.sleep(settings.scraper_request_delay_secs)

        return {
            "subs_scraped": len(target_map),
            "posts_seen": total_posts,
            "signals_found": total_signals,
        }

    finally:
        store.close()
