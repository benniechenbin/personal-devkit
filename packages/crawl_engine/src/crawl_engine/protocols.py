from __future__ import annotations

from typing import Protocol, runtime_checkable

from .schema import ScrapeRequest, ScrapeResponse


@runtime_checkable
class CrawlEngine(Protocol):
    """Protocol for synchronous page crawling engines."""

    def crawl(self, request: ScrapeRequest) -> ScrapeResponse:
        """Run a synchronous crawl request."""
        ...

    def close(self) -> None:
        """Release engine resources."""
        ...
