from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from crawl_engine.engines.crawl4ai_engine import Crawl4AIEngine
from crawl_engine.schema import Crawl4AIRequest, ScrapeResponse


class MarkdownFetchEngine(Protocol):
    async def fetch_content(self, request: Crawl4AIRequest) -> ScrapeResponse:
        ...


async def fetch_url_as_markdown(
    url: str,
    *,
    engine: MarkdownFetchEngine | None = None,
    headless: bool = True,
    remove_noise: bool = True,
    max_length: int = 20_000,
    wait_seconds: float | None = None,
    wait_for: str | None = None,
    js_code: Sequence[str] | None = None,
) -> ScrapeResponse:
    """
    Fetch a web page and return its cleaned Markdown content.

    This is a high-level convenience pipeline:
    URL -> Crawl4AIRequest -> Crawl4AIEngine -> ScrapeResponse.
    """
    final_js_code = list(js_code or [])

    if wait_seconds is not None and wait_seconds > 0:
        delay_ms = int(wait_seconds * 1000)
        final_js_code.insert(
            0,
            f"await new Promise(r => setTimeout(r, {delay_ms}));",
        )

    request = Crawl4AIRequest(
        url=url,
        remove_noise=remove_noise,
        max_length=max_length,
        wait_for=wait_for,
        js_code=final_js_code or None,
        metadata={
            "pipeline": "url_to_markdown",
        },
    )

    active_engine = engine or Crawl4AIEngine(headless=headless)
    return await active_engine.fetch_content(request)