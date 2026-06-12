from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from crawl_engine import AttachmentDownloader, AttachmentRequest

from subtitle_harvester_app.providers.base import SubtitleSearchResult

DEFAULT_MAX_SUBTITLE_PACKAGE_BYTES = 100 * 1024 * 1024


class DownloadedFileResult(Protocol):
    path: Path | None
    error_message: str | None


@dataclass(frozen=True)
class SubtitleDownloadResult:
    success: bool
    provider: str
    source_url: str
    output_dir: Path
    downloaded_file: DownloadedFileResult | None = None
    error_message: str | None = None

    @property
    def path(self) -> Path | None:
        if self.downloaded_file is None:
            return None
        return self.downloaded_file.path


class SubtitleDownloadManager:
    """通用字幕下载编排器。

    职责：
    - 接收统一的 SubtitleSearchResult；
    - 校验 download_url；
    - 调用 crawl_engine.AttachmentDownloader 下载到 raw/；
    - 返回结构化下载结果。

    不负责：
    - provider 专属 URL 拼接；
    - 解压；
    - 字幕文件筛选；
    - 字幕内容清洗；
    - 入库。
    """

    def __init__(self, downloader: AttachmentDownloader | None = None) -> None:
        self.downloader = downloader or AttachmentDownloader()

    async def close(self) -> None:
        await self.downloader.close()

    async def download(
        self,
        result: SubtitleSearchResult,
        output_dir: str | Path,
        *,
        max_size_bytes: int | None = DEFAULT_MAX_SUBTITLE_PACKAGE_BYTES,
        overwrite: bool = False,
        auto_rename: bool = True,
    ) -> SubtitleDownloadResult:
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        if not result.download_url:
            return SubtitleDownloadResult(
                success=False,
                provider=result.provider,
                source_url="",
                output_dir=target_dir,
                error_message="download_url is empty",
            )

        if not _is_absolute_url(result.download_url):
            return SubtitleDownloadResult(
                success=False,
                provider=result.provider,
                source_url=result.download_url,
                output_dir=target_dir,
                error_message=(
                    "download_url must be absolute; provider should resolve site-specific URLs."
                ),
            )

        downloaded = await self.downloader.download(
            AttachmentRequest(
                url=result.download_url,
                file_name=_resolve_file_name(result),
                max_size_bytes=max_size_bytes,
                metadata={
                    "provider": result.provider,
                    "media_type": result.media_type,
                    "tmdb_id": result.tmdb_id,
                    "imdb_id": result.imdb_id,
                    "title": result.title,
                    "year": result.year,
                    "language": result.language,
                    "source_id": result.source_id,
                    "season": result.season,
                    "episode": result.episode,
                },
            ),
            target_dir,
            overwrite=overwrite,
            auto_rename=auto_rename,
        )

        if not downloaded.success:
            return SubtitleDownloadResult(
                success=False,
                provider=result.provider,
                source_url=result.download_url,
                output_dir=target_dir,
                downloaded_file=downloaded,
                error_message=downloaded.error_message,
            )

        return SubtitleDownloadResult(
            success=True,
            provider=result.provider,
            source_url=result.download_url,
            output_dir=target_dir,
            downloaded_file=downloaded,
        )


def _resolve_file_name(result: SubtitleSearchResult) -> str:
    if result.file_name:
        return result.file_name

    title = result.title.strip() or "subtitle"
    language = result.language.strip() or "unknown"

    if result.season is not None and result.episode is not None:
        return f"{title}.S{result.season:02d}E{result.episode:02d}_{language}.zip"

    return f"{title}_{language}.zip"


def _is_absolute_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")
