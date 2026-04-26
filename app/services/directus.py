"""
Directus blog post publisher for the CircuitForge website CMS.

Directus runs in Docker on the website_cf-internal network and is not
directly reachable from host processes. We shell out to a one-shot
curlimages/curl container joined to that network.

Collection: blog_posts
Fields: id, title, slug, body, published_at, tags, author, seo_description

Environment variables (via Magpie .env):
    DIRECTUS_URL        Base URL inside the cf-internal network
                        (default: http://172.31.0.4:8055)
    DIRECTUS_ADMIN_TOKEN  Static admin token
    DIRECTUS_ADMIN_EMAIL  Admin email (for fresh JWT fallback)
    DIRECTUS_ADMIN_PASSWORD
    DIRECTUS_NETWORK    Docker network name
                        (default: website_cf-internal)

IP gotcha: 172.31.0.4 is the current cf-directus address on website_cf-internal.
If calls start returning connection errors run:
    docker inspect cf-directus --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
and update DIRECTUS_URL in Magpie's .env.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings

_CURL_IMAGE = "curlimages/curl:latest"


def _curl(method: str, path: str, token: str, body: dict[str, Any] | None = None) -> dict:
    """Run a curl request inside a container on the cf-internal network."""
    cfg = get_settings()
    url = f"{cfg.directus_url}{path}"
    cmd = [
        "docker", "run", "--rm",
        "--network", cfg.directus_network,
        _CURL_IMAGE,
        "-sf", "-X", method, url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
    ]
    if body is not None:
        cmd += ["--data", json.dumps(body)]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Directus {method} {path} failed: {result.stderr.strip()}")
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def _get_token() -> str:
    """Return a usable token: static admin token, or fresh JWT via login."""
    cfg = get_settings()
    if cfg.directus_admin_token:
        return cfg.directus_admin_token
    if not (cfg.directus_admin_email and cfg.directus_admin_password):
        raise RuntimeError(
            "No Directus credentials configured. "
            "Set DIRECTUS_ADMIN_TOKEN or DIRECTUS_ADMIN_EMAIL + DIRECTUS_ADMIN_PASSWORD."
        )
    resp = _curl("POST", "/auth/login", token="", body={
        "email": cfg.directus_admin_email,
        "password": cfg.directus_admin_password,
    })
    access_token = resp.get("data", {}).get("access_token")
    if not access_token:
        raise RuntimeError(f"Directus login failed: {resp}")
    return access_token


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def publish_blog_post(
    title: str,
    body: str,
    slug: str | None = None,
    tags: list[str] | None = None,
    author: str | None = None,
    seo_description: str | None = None,
    published_at: str | None = None,
) -> dict:
    """
    Create and publish a blog post in Directus.

    Returns the created item dict (id, slug, title, ...).

    published_at defaults to now (UTC ISO 8601). Pass None or omit to publish
    immediately. Pass a future timestamp to schedule.
    """
    token = _get_token()

    _slug = slug or slugify(title)
    _published_at = published_at or datetime.now(timezone.utc).isoformat()

    payload: dict[str, Any] = {
        "title": title,
        "slug": _slug,
        "body": body,
        "published_at": _published_at,
    }
    if tags:
        payload["tags"] = tags
    if author:
        payload["author"] = author
    if seo_description:
        payload["seo_description"] = seo_description

    resp = _curl("POST", "/items/blog_posts", token=token, body=payload)
    item = resp.get("data", resp)
    return item


def get_blog_post(slug: str) -> dict | None:
    """Fetch a blog post by slug. Returns None if not found."""
    from urllib.parse import quote
    token = _get_token()
    # Directus filter syntax uses brackets which must be percent-encoded for curl CLI
    filter_param = f"filter%5Bslug%5D%5B_eq%5D={quote(slug, safe='')}"
    resp = _curl(
        "GET",
        f"/items/blog_posts?{filter_param}&limit=1",
        token=token,
    )
    items = resp.get("data", [])
    return items[0] if items else None


def update_blog_post(post_id: int, fields: dict[str, Any]) -> dict:
    """Patch an existing blog post by ID."""
    token = _get_token()
    resp = _curl("PATCH", f"/items/blog_posts/{post_id}", token=token, body=fields)
    return resp.get("data", resp)
