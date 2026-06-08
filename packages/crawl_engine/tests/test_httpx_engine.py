from __future__ import annotations

import asyncio

import httpx
from crawl_engine.engines.httpx_engine import HttpxEngine
from crawl_engine.schema import ScrapeRequest


def test_httpx_engine_fetches_html_successfully() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("x-test") == "yes"
            return httpx.Response(
                200,
                text="<html><body>Hello</body></html>",
                headers={"content-type": "text/html; charset=utf-8"},
                request=request,
            )

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport)
        engine = HttpxEngine(client=client)

        try:
            response = await engine.fetch_content(
                ScrapeRequest(
                    url="https://example.com/demo",
                    headers={"X-Test": "yes"},
                )
            )
        finally:
            await engine.close()

        assert response.success is True
        assert response.url == "https://example.com/demo"
        assert response.final_url == "https://example.com/demo"
        assert response.status_code == 200
        assert response.content_type == "text/html; charset=utf-8"
        assert response.raw_html == "<html><body>Hello</body></html>"
        assert response.content == "<html><body>Hello</body></html>"
        assert response.content_length == len("<html><body>Hello</body></html>")
        assert response.error_message is None

    asyncio.run(run())


def test_httpx_engine_returns_failure_on_http_error() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                500,
                text="server error",
                headers={"content-type": "text/plain"},
                request=request,
            )

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport)
        engine = HttpxEngine(client=client)

        try:
            response = await engine.fetch_content(ScrapeRequest(url="https://example.com/error"))
        finally:
            await engine.close()

        assert response.success is False
        assert response.url == "https://example.com/error"
        assert response.final_url == "https://example.com/error"
        assert response.status_code == 500
        assert response.content_type == "text/plain"
        assert response.error_message == "HTTP 500"

    asyncio.run(run())


def test_httpx_engine_returns_failure_on_timeout() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timeout", request=request)

        transport = httpx.MockTransport(handler)
        client = httpx.AsyncClient(transport=transport)
        engine = HttpxEngine(client=client)

        try:
            response = await engine.fetch_content(ScrapeRequest(url="https://example.com/timeout"))
        finally:
            await engine.close()

        assert response.success is False
        assert response.url == "https://example.com/timeout"
        assert response.error_message == "Timeout"

    asyncio.run(run())
