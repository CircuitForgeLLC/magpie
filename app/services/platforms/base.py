from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PostResult:
    url: str
    metadata: dict | None = field(default=None)


class PostingStrategy(ABC):
    """Base class for all posting output types.

    Subclasses must set class attribute `campaign_type` matching the value
    stored in campaigns.type.
    """

    campaign_type: str  # e.g. "reddit_post", "reddit_comment", "blog_post"

    @abstractmethod
    def execute(
        self,
        *,
        target: str,
        title: str,
        body: str,
        flair: str | None = None,
        extra: dict | None = None,
    ) -> PostResult:
        """Execute the post. Raise on failure. Return PostResult on success."""
        ...

    def supports_dupe_guard(self) -> bool:
        """Return False to skip the weekly-dupe-guard check for this type."""
        return True
