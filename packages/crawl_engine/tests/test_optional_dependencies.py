from __future__ import annotations


def test_import_crawl_engine_without_crawl4ai_runtime_dependency() -> None:
    import crawl_engine

    assert crawl_engine.__version__ == "0.2.1"


def test_import_httpx_engine_from_public_api() -> None:
    from crawl_engine import (
        ArchiveExtractor,
        ArchiveRequest,
        AttachmentDownloader,
        AttachmentRequest,
        Crawl4AIEngine,
        DownloadedFile,
        ExtractedArchive,
        ExtractedFile,
        HttpxEngine,
        ScrapeRequest,
        ScrapeResponse,
    )

    assert ArchiveExtractor is not None
    assert ArchiveRequest is not None
    assert AttachmentDownloader is not None
    assert AttachmentRequest is not None
    assert Crawl4AIEngine is not None
    assert DownloadedFile is not None
    assert ExtractedArchive is not None
    assert ExtractedFile is not None
    assert HttpxEngine is not None
    assert ScrapeRequest is not None
    assert ScrapeResponse is not None


def test_import_engines_from_subpackage_api() -> None:
    from crawl_engine.engines import Crawl4AIEngine, HttpxEngine

    assert Crawl4AIEngine is not None
    assert HttpxEngine is not None


def test_import_crawl4ai_engine_does_not_execute_crawl4ai_import() -> None:
    from crawl_engine.engines.crawl4ai_engine import Crawl4AIEngine

    engine = Crawl4AIEngine(headless=True)

    assert engine.headless is True
