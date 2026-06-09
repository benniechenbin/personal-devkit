from __future__ import annotations

import asyncio

from crawl_engine.pipelines.url_to_markdown import fetch_url_as_markdown
from crawl_engine.schema import Crawl4AIRequest, ScrapeResponse


class FakeMarkdownEngine:
    def __init__(self) -> None:
        self.request: Crawl4AIRequest | None = None

    async def fetch_content(self, request: Crawl4AIRequest) -> ScrapeResponse:
        self.request = request
        return ScrapeResponse(
            success=True,
            url=request.url,
            content="# Demo\n\nHello",
            raw_html="<html>Hello</html>",
            content_length=len("# Demo\n\nHello"),
            metadata={"engine": "fake"},
        )


def test_fetch_url_as_markdown_builds_crawl4ai_request() -> None:
    async def run() -> None:
        engine = FakeMarkdownEngine()

        response = await fetch_url_as_markdown(
            "https://example.com/page",
            engine=engine,
            max_length=12_000,
            wait_seconds=1.5,
            wait_for="css:.content",
            js_code=["console.log('ready');"],
        )

        assert response.success is True
        assert response.content == "# Demo\n\nHello"

        assert engine.request is not None
        assert engine.request.url == "https://example.com/page"
        assert engine.request.max_length == 12_000
        assert engine.request.wait_for == "css:.content"
        assert engine.request.remove_noise is True
        assert engine.request.metadata == {"pipeline": "url_to_markdown"}

        assert engine.request.js_code is not None
        assert "setTimeout" in engine.request.js_code[0]
        assert "1500" in engine.request.js_code[0]
        assert engine.request.js_code[1] == "console.log('ready');"

    asyncio.run(run())


def test_fetch_url_as_markdown_without_wait_seconds() -> None:
    async def run() -> None:
        engine = FakeMarkdownEngine()

        await fetch_url_as_markdown(
            "https://example.com/page",
            engine=engine,
            wait_seconds=None,
            js_code=None,
        )

        assert engine.request is not None
        assert engine.request.js_code is None

    asyncio.run(run())
