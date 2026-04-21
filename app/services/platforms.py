"""
Platform registry: maps platform names to their poster implementations.

Adding a new platform:
  1. Create app/services/<platform>/client.py implementing PlatformClient
  2. Register it here in REGISTRY

This keeps poster.py platform-agnostic — it looks up the right client by
the campaign's `platform` field rather than branching on strings everywhere.
"""
from __future__ import annotations

from typing import Protocol


class PlatformClient(Protocol):
    def post(self, target: str, title: str, body: str, flair: str | None = None) -> str:
        """Post content to a target (sub, group, channel). Returns a URL."""
        ...


def get_client(platform: str) -> PlatformClient:
    """Return an initialized client for the given platform name."""
    if platform == "reddit":
        from app.services.reddit.client import RedditClient
        return RedditClient()
    raise NotImplementedError(
        f"Platform '{platform}' is not yet implemented. "
        f"Add a client in app/services/{platform}/ and register it here."
    )


# Platforms with posting support implemented
SUPPORTED_PLATFORMS = {"reddit"}

# Platforms planned but not yet implemented
PLANNED_PLATFORMS = {"facebook", "discord", "lemmy", "mastodon"}
