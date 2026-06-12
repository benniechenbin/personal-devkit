from __future__ import annotations

import asyncio

import httpx
from crawl_engine.downloads import AttachmentDownloader
from crawl_engine.downloads.attachment_downloader import DEFAULT_CHUNK_SIZE
from crawl_engine.schema import AttachmentRequest


class ChunkedStream(httpx.AsyncByteStream):
    def __init__(self, chunks: list[bytes]) -> None:
        self.chunks = chunks

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk


def test_attachment_downloader_saves_file_with_explicit_name(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("x-token") == "demo"
            return httpx.Response(
                200,
                content=b"PDF content",
                headers={"content-type": "application/pdf"},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(
                    url="https://example.com/files/report",
                    file_name="报告:附件?.pdf",
                    headers={"X-Token": "demo"},
                    metadata={"source": "test"},
                ),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is True
        assert result.path is not None
        assert result.path.exists()
        assert result.path.read_bytes() == b"PDF content"
        assert result.file_name == "报告_附件.pdf"
        assert result.content_type == "application/pdf"
        assert result.size_bytes == len(b"PDF content")
        assert result.metadata == {"source": "test"}

    asyncio.run(run())


def test_attachment_downloader_uses_content_disposition_filename(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"hello",
                headers={
                    "content-type": "application/octet-stream",
                    "content-disposition": 'attachment; filename="demo.pdf"',
                },
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(url="https://example.com/download"),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is True
        assert result.path is not None
        assert result.path.name == "demo.pdf"
        assert result.path.read_bytes() == b"hello"

    asyncio.run(run())


def test_attachment_downloader_streams_response_to_file(tmp_path) -> None:
    async def run() -> None:
        chunks = [b"a" * DEFAULT_CHUNK_SIZE, b"tail"]

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                stream=ChunkedStream(chunks),
                headers={"content-type": "application/octet-stream"},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(
                    url="https://example.com/files/large.bin",
                ),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is True
        assert result.path is not None
        assert result.size_bytes == DEFAULT_CHUNK_SIZE + len(b"tail")
        assert result.path.read_bytes() == b"".join(chunks)
        assert not list(tmp_path.glob("*.part"))

    asyncio.run(run())


def test_attachment_downloader_rejects_content_length_over_limit(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"too big",
                headers={
                    "content-length": "7",
                    "content-type": "application/octet-stream",
                },
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(
                    url="https://example.com/files/large.bin",
                    max_size_bytes=4,
                ),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is False
        assert result.path == tmp_path / "large.bin"
        assert result.error_message == "附件大小超过限制：7 > 4"
        assert not (tmp_path / "large.bin").exists()
        assert not list(tmp_path.glob("*.part"))

    asyncio.run(run())


def test_attachment_downloader_stops_stream_when_size_limit_is_exceeded(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                stream=ChunkedStream([b"abc", b"de"]),
                headers={"content-type": "application/octet-stream"},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(
                    url="https://example.com/files/large.bin",
                    max_size_bytes=4,
                ),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is False
        assert result.path == tmp_path / "large.bin"
        assert result.error_message == "附件大小超过限制：5 > 4"
        assert not (tmp_path / "large.bin").exists()
        assert not list(tmp_path.glob("*.part"))

    asyncio.run(run())


def test_attachment_downloader_uses_url_filename_when_no_explicit_name(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"data",
                headers={"content-type": "application/pdf"},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(url="https://example.com/files/demo.pdf"),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is True
        assert result.path is not None
        assert result.path.name == "demo.pdf"
        assert result.path.read_bytes() == b"data"

    asyncio.run(run())


def test_attachment_downloader_auto_renames_existing_file(tmp_path) -> None:
    async def run() -> None:
        (tmp_path / "demo.pdf").write_bytes(b"old")

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"new",
                headers={"content-type": "application/pdf"},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(
                    url="https://example.com/files/demo.pdf",
                ),
                tmp_path,
                auto_rename=True,
            )
        finally:
            await downloader.close()

        assert result.success is True
        assert result.path is not None
        assert result.path.name == "demo_1.pdf"
        assert result.path.read_bytes() == b"new"
        assert (tmp_path / "demo.pdf").read_bytes() == b"old"

    asyncio.run(run())


def test_attachment_downloader_returns_failure_when_file_exists_without_overwrite(
    tmp_path,
) -> None:
    async def run() -> None:
        existing = tmp_path / "demo.pdf"
        existing.write_bytes(b"old")

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"new",
                headers={"content-type": "application/pdf"},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(url="https://example.com/files/demo.pdf"),
                tmp_path,
                overwrite=False,
                auto_rename=False,
            )
        finally:
            await downloader.close()

        assert result.success is False
        assert result.path == existing
        assert result.error_message is not None
        assert "文件已存在" in result.error_message
        assert existing.read_bytes() == b"old"

    asyncio.run(run())


def test_attachment_downloader_overwrites_existing_file_when_requested(tmp_path) -> None:
    async def run() -> None:
        existing = tmp_path / "demo.pdf"
        existing.write_bytes(b"old")

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=b"new",
                headers={"content-type": "application/pdf"},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(url="https://example.com/files/demo.pdf"),
                tmp_path,
                overwrite=True,
                auto_rename=False,
            )
        finally:
            await downloader.close()

        assert result.success is True
        assert result.path == existing
        assert existing.read_bytes() == b"new"

    asyncio.run(run())


def test_attachment_downloader_returns_failure_on_http_error(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                404,
                content=b"not found",
                headers={"content-type": "text/plain"},
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(url="https://example.com/missing.pdf"),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is False
        assert result.error_message == "HTTP 404"
        assert result.content_type == "text/plain"

    asyncio.run(run())


def test_attachment_downloader_returns_failure_on_timeout(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timeout", request=request)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(url="https://example.com/timeout.pdf"),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is False
        assert result.error_message == "下载超时"
        assert result.file_name == ""

    asyncio.run(run())


def test_attachment_downloader_returns_failure_on_unexpected_error(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise RuntimeError("boom")

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            result = await downloader.download(
                AttachmentRequest(
                    url="https://example.com/error.pdf",
                    file_name="error.pdf",
                ),
                tmp_path,
            )
        finally:
            await downloader.close()

        assert result.success is False
        assert result.error_message == "boom"
        assert result.file_name == "error.pdf"

    asyncio.run(run())


def test_attachment_downloader_download_many(tmp_path) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                content=request.url.path.encode("utf-8"),
                request=request,
            )

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        downloader = AttachmentDownloader(client=client)

        try:
            results = await downloader.download_many(
                [
                    AttachmentRequest(url="https://example.com/a.pdf"),
                    AttachmentRequest(url="https://example.com/b.pdf"),
                ],
                tmp_path,
            )
        finally:
            await downloader.close()

        assert [result.success for result in results] == [True, True]
        assert [result.file_name for result in results] == ["a.pdf", "b.pdf"]
        assert (tmp_path / "a.pdf").read_bytes() == b"/a.pdf"
        assert (tmp_path / "b.pdf").read_bytes() == b"/b.pdf"

    asyncio.run(run())
