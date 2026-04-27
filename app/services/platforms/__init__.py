from __future__ import annotations

from app.services.platforms.base import PostingStrategy, PostResult
from app.services.platforms.reddit_post import RedditPostStrategy
from app.services.platforms.reddit_comment import RedditCommentStrategy

_REGISTRY: dict[str, PostingStrategy] = {
    s.campaign_type: s()
    for s in [
        RedditPostStrategy,
        RedditCommentStrategy,
        # BlogPostStrategy — added in Plan C
    ]
}

SUPPORTED_PLATFORMS: frozenset[str] = frozenset(_REGISTRY)


def get_client(campaign_type: str) -> PostingStrategy:
    """Return the strategy instance for the given campaign type.

    Raises ValueError for unknown types.
    """
    if campaign_type not in _REGISTRY:
        raise ValueError(f"Unknown campaign type: {campaign_type!r}")
    return _REGISTRY[campaign_type]


__all__ = ["get_client", "SUPPORTED_PLATFORMS", "PostingStrategy", "PostResult"]
