from __future__ import annotations

import asyncio
import json
import zipfile
from pathlib import Path

from crawl_engine import DownloadedFile

from subtitle_harvester_app.downloads.download_manager import SubtitleDownloadResult
from subtitle_harvester_app.pipelines.subtitle_acquire_pipeline import (
    SubtitleAcquirePipeline,
    rank_results,
    select_best_result,
)
from subtitle_harvester_app.providers.base import SubtitleSearchResult
from subtitle_harvester_app.schema import MediaCandidate


def _candidate() -> MediaCandidate:
    return MediaCandidate(
        media_type="movie",
        tmdb_id=980477,
        imdb_id="tt0000001",
        title="Demo Movie",
        original_title="Demo Movie",
        year=2026,
        release_date="2026-06-01",
        original_language="zh",
        overview=None,
        aliases=[],
    )


def _result(
    *,
    score: float = 80.0,
    download_url: str | None = "https://example.com/demo.zip",
    file_name: str | None = "demo.zip",
    language: str = "zh",
) -> SubtitleSearchResult:
    return SubtitleSearchResult(
        provider="subdl",
        media_type="movie",
        tmdb_id=980477,
        imdb_id="tt0000001",
        title="Demo Movie",
        year=2026,
        language=language,
        release_name="Demo.Movie.2026",
        file_name=file_name,
        download_url=download_url,
        source_id="sub-1",
        score=score,
        raw={"id": "sub-1"},
    )


class FakeDownloadManager:
    async def close(self) -> None:
        return None

    async def download(
        self,
        result: SubtitleSearchResult,
        output_dir: str | Path,
        *,
        max_size_bytes: int | None = None,
        overwrite: bool = False,
        auto_rename: bool = True,
    ) -> SubtitleDownloadResult:
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        archive_path = target_dir / (result.file_name or "demo.zip")
        with zipfile.ZipFile(archive_path, "w") as zip_file:
            zip_file.writestr(
                "demo.zh.srt",
                "1\n00:00:01,000 --> 00:00:02,000\n你好\n",
            )
            zip_file.writestr("readme.txt", "ignore me")

        downloaded = DownloadedFile(
            success=True,
            url=result.download_url or "",
            path=archive_path,
            file_name=archive_path.name,
            content_type="application/zip",
            size_bytes=archive_path.stat().st_size,
            metadata={"provider": result.provider},
        )

        return SubtitleDownloadResult(
            success=True,
            provider=result.provider,
            source_url=result.download_url or "",
            output_dir=target_dir,
            downloaded_file=downloaded,
        )


class FailingDownloadManager:
    async def close(self) -> None:
        return None

    async def download(
        self,
        result: SubtitleSearchResult,
        output_dir: str | Path,
        *,
        max_size_bytes: int | None = None,
        overwrite: bool = False,
        auto_rename: bool = True,
    ) -> SubtitleDownloadResult:
        return SubtitleDownloadResult(
            success=False,
            provider=result.provider,
            source_url=result.download_url or "",
            output_dir=Path(output_dir),
            error_message="download failed",
        )


class FailFirstDownloadManager:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def close(self) -> None:
        return None

    async def download(
        self,
        result: SubtitleSearchResult,
        output_dir: str | Path,
        *,
        max_size_bytes: int | None = None,
        overwrite: bool = False,
        auto_rename: bool = True,
    ) -> SubtitleDownloadResult:
        self.calls.append(result.file_name or "")

        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        if result.file_name == "first.zip":
            return SubtitleDownloadResult(
                success=False,
                provider=result.provider,
                source_url=result.download_url or "",
                output_dir=target_dir,
                error_message="HTTP 404",
            )

        archive_path = target_dir / (result.file_name or "fallback.zip")
        with zipfile.ZipFile(archive_path, "w") as zip_file:
            zip_file.writestr(
                "fallback.zh.srt",
                "1\n00:00:01,000 --> 00:00:02,000\n你好\n",
            )

        downloaded = DownloadedFile(
            success=True,
            url=result.download_url or "",
            path=archive_path,
            file_name=archive_path.name,
            content_type="application/zip",
            size_bytes=archive_path.stat().st_size,
            metadata={"provider": result.provider},
        )

        return SubtitleDownloadResult(
            success=True,
            provider=result.provider,
            source_url=result.download_url or "",
            output_dir=target_dir,
            downloaded_file=downloaded,
        )


class CountingDownloadManager(FakeDownloadManager):
    def __init__(self) -> None:
        self.calls = 0

    async def download(
        self,
        result: SubtitleSearchResult,
        output_dir: str | Path,
        *,
        max_size_bytes: int | None = None,
        overwrite: bool = False,
        auto_rename: bool = True,
    ) -> SubtitleDownloadResult:
        self.calls += 1
        return await super().download(
            result,
            output_dir,
            max_size_bytes=max_size_bytes,
            overwrite=overwrite,
            auto_rename=auto_rename,
        )


def test_select_best_result_chooses_highest_score_downloadable_result() -> None:
    low = _result(score=50.0, file_name="low.zip")
    high = _result(score=90.0, file_name="high.zip")
    no_url = _result(score=100.0, download_url=None, file_name="no-url.zip")

    selected = select_best_result([low, high, no_url], min_score=0)

    assert selected == high


def test_select_best_result_returns_none_when_below_min_score() -> None:
    selected = select_best_result([_result(score=50.0)], min_score=60.0)

    assert selected is None


def test_subtitle_acquire_pipeline_downloads_and_processes_best_result(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        pipeline = SubtitleAcquirePipeline(
            download_manager=FakeDownloadManager(),  # type: ignore[arg-type]
        )

        result = await pipeline.acquire(
            _candidate(),
            [
                _result(score=40.0, file_name="low.zip"),
                _result(score=90.0, file_name="best.zip"),
            ],
            tmp_path,
            min_score=60.0,
        )

        assert result.success is True
        assert result.selected_result is not None
        assert result.selected_result.file_name == "best.zip"

        assert result.media_dir == tmp_path / "subtitles" / "inbox" / "movie_980477"
        assert result.raw_dir == result.media_dir / "raw"
        assert result.extracted_dir == result.media_dir / "extracted"

        assert result.download_result is not None
        assert result.download_result.path == result.raw_dir / "best.zip"

        assert result.package_result is not None
        assert result.package_result.success is True
        assert [path.name for path in result.subtitle_files] == ["demo.zh.srt"]

        assert (result.raw_dir / "best.zip").exists()
        assert (
            (result.extracted_dir / "best" / "demo.zh.srt")
            .read_text(encoding="utf-8")
            .endswith("你好\n")
        )

    asyncio.run(run())


def test_subtitle_acquire_pipeline_skips_when_no_downloadable_result(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        pipeline = SubtitleAcquirePipeline(
            download_manager=FakeDownloadManager(),  # type: ignore[arg-type]
        )

        result = await pipeline.acquire(
            _candidate(),
            [_result(score=90.0, download_url=None)],
            tmp_path,
        )

        assert result.success is False
        assert result.selected_result is None
        assert result.download_result is None
        assert result.package_result is None
        assert result.error_message == "没有可下载的字幕结果。"

    asyncio.run(run())


def test_subtitle_acquire_pipeline_returns_download_failure(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        pipeline = SubtitleAcquirePipeline(
            download_manager=FailingDownloadManager(),  # type: ignore[arg-type]
        )

        result = await pipeline.acquire(
            _candidate(),
            [_result(score=90.0)],
            tmp_path,
        )

        assert result.success is False
        assert result.selected_result is not None
        assert result.download_result is not None
        assert result.package_result is None
        assert result.error_message == "download failed"

    asyncio.run(run())


def test_select_best_result_prefers_chinese_over_higher_scored_english() -> None:
    english = _result(
        score=95.0,
        language="English",
        file_name="Demo.Movie.2026.English.zip",
    )
    chinese = _result(
        score=70.0,
        language="Chinese",
        file_name="Demo.Movie.2026.Chinese.zip",
    )

    selected = select_best_result(
        [english, chinese],
        min_score=0,
        preferred_languages=("zh", "chinese"),
    )

    assert selected == chinese


def test_select_best_result_allows_large_quality_gap_to_win() -> None:
    english = _result(
        score=120.0,
        language="English",
        file_name="Demo.Movie.2026.English.zip",
    )
    chinese = _result(
        score=70.0,
        language="Chinese",
        file_name="Demo.Movie.2026.Chinese.zip",
    )

    selected = select_best_result(
        [english, chinese],
        min_score=0,
        preferred_languages=("zh", "chinese"),
    )

    assert selected == english


def test_select_best_result_falls_back_to_highest_score_when_no_chinese() -> None:
    english = _result(
        score=95.0,
        language="English",
        file_name="Demo.Movie.2026.English.zip",
    )
    japanese = _result(
        score=70.0,
        language="Japanese",
        file_name="Demo.Movie.2026.Japanese.zip",
    )

    selected = select_best_result(
        [japanese, english],
        min_score=0,
        preferred_languages=("zh", "chinese"),
    )

    assert selected == english


def test_subtitle_acquire_pipeline_prefers_chinese_result(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        pipeline = SubtitleAcquirePipeline(
            download_manager=FakeDownloadManager(),  # type: ignore[arg-type]
            preferred_languages=("zh", "chinese"),
        )

        result = await pipeline.acquire(
            _candidate(),
            [
                _result(
                    score=95.0,
                    language="English",
                    file_name="english.zip",
                ),
                _result(
                    score=70.0,
                    language="Chinese",
                    file_name="chinese.zip",
                ),
            ],
            tmp_path,
            min_score=0,
        )

        assert result.success is True
        assert result.selected_result is not None
        assert result.selected_result.file_name == "chinese.zip"
        assert result.download_result is not None
        assert result.download_result.path == result.raw_dir / "chinese.zip"

    asyncio.run(run())


def test_rank_results_prefers_chinese_then_score() -> None:
    english_high = _result(
        score=95.0,
        language="English",
        file_name="english-high.zip",
    )
    chinese_low = _result(
        score=70.0,
        language="Chinese",
        file_name="chinese-low.zip",
    )
    chinese_high = _result(
        score=90.0,
        language="Chinese",
        file_name="chinese-high.zip",
    )

    ranked = rank_results(
        [english_high, chinese_low, chinese_high],
        preferred_languages=("zh", "chinese"),
    )

    assert [item.file_name for item in ranked] == [
        "chinese-high.zip",
        "chinese-low.zip",
        "english-high.zip",
    ]


def test_subtitle_acquire_pipeline_tries_next_result_after_download_failure(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        download_manager = FailFirstDownloadManager()
        pipeline = SubtitleAcquirePipeline(
            download_manager=download_manager,  # type: ignore[arg-type]
            preferred_languages=("zh", "chinese"),
        )

        result = await pipeline.acquire(
            _candidate(),
            [
                _result(
                    score=90.0,
                    language="Chinese",
                    file_name="first.zip",
                ),
                _result(
                    score=80.0,
                    language="Chinese",
                    file_name="fallback.zip",
                ),
            ],
            tmp_path,
            min_score=0,
        )

        assert result.success is True
        assert result.selected_result is not None
        assert result.selected_result.file_name == "fallback.zip"

        assert download_manager.calls == ["first.zip", "fallback.zip"]

        assert len(result.attempts) == 2
        assert result.attempts[0].error_message == "HTTP 404"
        assert result.attempts[1].error_message is None

        assert result.download_result is not None
        assert result.download_result.path == result.raw_dir / "fallback.zip"

        assert [path.name for path in result.subtitle_files] == ["fallback.zh.srt"]

    asyncio.run(run())


def test_subtitle_acquire_pipeline_reuses_manifest_without_redownloading(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        download_manager = CountingDownloadManager()
        pipeline = SubtitleAcquirePipeline(
            download_manager=download_manager,  # type: ignore[arg-type]
        )

        first = await pipeline.acquire(
            _candidate(),
            [_result(score=90.0, file_name="best.zip")],
            tmp_path,
        )
        second = await pipeline.acquire(
            _candidate(),
            [_result(score=90.0, file_name="best.zip")],
            tmp_path,
        )

        assert first.success is True
        assert second.success is True
        assert download_manager.calls == 1
        assert second.download_result is None
        assert [path.name for path in second.subtitle_files] == ["demo.zh.srt"]
        manifest_path = second.media_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema_version"] == 1
        assert manifest["status"] == "success"
        assert manifest["provider"] == "subdl"
        assert manifest["source_id"] == "sub-1"
        assert manifest["created_at"]

    asyncio.run(run())


def test_subtitle_acquire_pipeline_ignores_incompatible_manifest(
    tmp_path: Path,
) -> None:
    async def run() -> None:
        media_dir = tmp_path / "subtitles" / "inbox" / "movie_980477"
        media_dir.mkdir(parents=True)
        (media_dir / "manifest.json").write_text(
            json.dumps({"schema_version": 999, "status": "success"}),
            encoding="utf-8",
        )

        download_manager = CountingDownloadManager()
        pipeline = SubtitleAcquirePipeline(
            download_manager=download_manager,  # type: ignore[arg-type]
        )

        result = await pipeline.acquire(
            _candidate(),
            [_result(score=90.0, file_name="best.zip")],
            tmp_path,
        )

        assert result.success is True
        assert download_manager.calls == 1

    asyncio.run(run())
