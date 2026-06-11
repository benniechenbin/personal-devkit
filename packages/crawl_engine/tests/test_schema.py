from __future__ import annotations

from crawl_engine.schema import (
    AttachmentRequest,
    Crawl4AIRequest,
    ScrapeRequest,
    ScrapeResponse,
)


def test_scrape_request_defaults() -> None:
    request = ScrapeRequest(url="https://example.com")

    assert request.url == "https://example.com"
    assert request.headers == {}
    assert request.timeout_ms == 30_000
    assert request.metadata == {}


def test_scrape_response_supports_extended_fields() -> None:
    response = ScrapeResponse(
        success=True,
        url="https://example.com",
        final_url="https://example.com/final",
        status_code=200,
        content_type="text/html",
        content="hello",
        raw_html="<html>hello</html>",
        content_length=5,
        extracted_data={"title": "demo"},
        metadata={"engine": "httpx"},
    )

    assert response.success is True
    assert response.status_code == 200
    assert response.final_url == "https://example.com/final"
    assert response.content_type == "text/html"
    assert response.extracted_data == {"title": "demo"}
    assert response.metadata == {"engine": "httpx"}


def test_crawl4ai_request_defaults() -> None:
    request = Crawl4AIRequest(url="https://example.com")

    assert request.remove_noise is True
    assert request.max_length == 10_000
    assert request.css_schema is None
    assert request.wait_for is None
    assert request.js_code is None


def test_attachment_request_defaults() -> None:
    request = AttachmentRequest(url="https://example.com/file.zip")

    assert request.url == "https://example.com/file.zip"
    assert request.file_name is None
    assert request.headers == {}
    assert request.timeout_ms == 30_000
    assert request.max_size_bytes is None
    assert request.metadata == {}
