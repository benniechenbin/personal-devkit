from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
from crawl_engine import AttachmentDownloader

from subtitle_harvester_app.downloads.download_manager import SubtitleDownloadManager
from subtitle_harvester_app.providers.base import SubtitleSearchResult


def _search_result(
    *,
    download_url: str | None = "https://example.com/subtitles/demo.zip",
    file_name: str | None = "demo.zip",
) -> SubtitleSearchResult:
    return SubtitleSearchResult(
        provider="subdl",
        media_type="movie",
        tmdb_id=1,
        imdb_id="tt0000001",
        title="Demo",
        year=2026,
        language="zh",
        release_name="Demo.Release",
        file_name=file_name,
        download_url=download_url,
        source_id="source-1",
        score=90.0,
        raw={"id": "source-1"},
    )


def test_download_manager_downloads_subtitle_package(tmp_path: Path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == "https://example.com/subtitles/demo.zip"
            return httpx.Response(
                200,
                content=b"zip-content",
                headers={"content-type": "application/zip"},
                request=request,
            )

        http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=http_client)
        manager = SubtitleDownloadManager(downloader=downloader)

        try:
            result = await manager.download(
                _search_result(),
                tmp_path / "raw",
            )
        finally:
            await manager.close()

        assert result.success is True
        assert result.provider == "subdl"
        assert result.source_url == "https://example.com/subtitles/demo.zip"
        assert result.path == tmp_path / "raw" / "demo.zip"
        assert result.path is not None
        assert result.path.read_bytes() == b"zip-content"

        assert result.downloaded_file is not None
        assert result.downloaded_file.metadata["provider"] == "subdl"
        assert result.downloaded_file.metadata["tmdb_id"] == 1
        assert result.downloaded_file.metadata["title"] == "Demo"

    asyncio.run(run())


def test_download_manager_uses_generated_filename_when_missing(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"zip-content",
                headers={"content-type": "application/zip"},
                request=request,
            )

        http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=http_client)
        manager = SubtitleDownloadManager(downloader=downloader)

        try:
            result = await manager.download(
                _search_result(file_name=None),
                tmp_path / "raw",
            )
        finally:
            await manager.close()

        assert result.success is True
        assert result.path == tmp_path / "raw" / "Demo_zh.zip"

    asyncio.run(run())


def test_download_manager_rejects_missing_download_url(tmp_path: Path) -> None:
    async def run() -> None:
        manager = SubtitleDownloadManager()

        try:
            result = await manager.download(
                _search_result(download_url=None),
                tmp_path / "raw",
            )
        finally:
            await manager.close()

        assert result.success is False
        assert result.path is None
        assert result.error_message == "download_url is empty"

    asyncio.run(run())


def test_download_manager_rejects_relative_download_url(tmp_path: Path) -> None:
    async def run() -> None:
        manager = SubtitleDownloadManager()

        try:
            result = await manager.download(
                _search_result(download_url="/download/demo.zip"),
                tmp_path / "raw",
            )
        finally:
            await manager.close()

        assert result.success is False
        assert result.path is None
        assert result.error_message == (
            "download_url must be absolute; provider should resolve site-specific URLs."
        )

    asyncio.run(run())


def test_download_manager_returns_failure_on_http_error(tmp_path: Path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                404,
                content=b"not found",
                headers={"content-type": "text/plain"},
                request=request,
            )

        http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=http_client)
        manager = SubtitleDownloadManager(downloader=downloader)

        try:
            result = await manager.download(
                _search_result(download_url="https://example.com/missing.zip"),
                tmp_path / "raw",
            )
        finally:
            await manager.close()

        assert result.success is False
        assert result.downloaded_file is not None
        assert result.downloaded_file.path is None
        assert result.downloaded_file.file_name == "demo.zip"
        assert result.error_message == "HTTP 404"

    asyncio.run(run())
