from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from subtitle_harvester_app.downloads.download_manager import (
    DEFAULT_MAX_SUBTITLE_PACKAGE_BYTES,
    SubtitleDownloadManager,
    SubtitleDownloadResult,
)
from subtitle_harvester_app.downloads.package_processor import (
    ProcessedSubtitlePackage,
    SubtitlePackageProcessor,
)
from subtitle_harvester_app.providers.base import SubtitleSearchResult
from subtitle_harvester_app.schema import MediaCandidate

DEFAULT_PREFERRED_LANGUAGES = (
    "zh",
    "zh-cn",
    "zh-hans",
    "zh-hant",
    "chinese",
    "mandarin",
    "中文",
    "简体中文",
    "繁體中文",
)

_LANGUAGE_ALIASES: dict[str, set[str]] = {
    "zh": {
        "zh",
        "zho",
        "chi",
        "chs",
        "cht",
        "cn",
        "zhcn",
        "zhhans",
        "zhhant",
        "chinese",
        "mandarin",
        "中文",
        "简体",
        "繁体",
        "简体中文",
        "繁體中文",
    },
    "en": {
        "en",
        "eng",
        "english",
    },
}


def _language_terms(*values: str | None) -> set[str]:
    terms: set[str] = set()

    for value in values:
        if not value:
            continue

        text = value.lower()
        compact = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text)
        if compact:
            terms.add(compact)

        for token in re.split(r"[^a-z0-9\u4e00-\u9fff]+", text):
            if token:
                terms.add(token)

    return terms


def _expand_language_aliases(language: str) -> set[str]:
    terms = _language_terms(language)
    expanded = set(terms)

    for term in terms:
        expanded.update(_LANGUAGE_ALIASES.get(term, set()))

    return expanded


def _matches_preferred_language(
    result: SubtitleSearchResult,
    preferred_languages: Sequence[str],
) -> bool:
    result_terms = _language_terms(
        result.language,
        result.file_name,
        result.release_name,
    )

    preferred_terms: set[str] = set()
    for language in preferred_languages:
        preferred_terms.update(_expand_language_aliases(language))

    return bool(result_terms & preferred_terms)


@dataclass(frozen=True)
class SubtitleAcquireAttempt:
    selected_result: SubtitleSearchResult
    download_result: SubtitleDownloadResult | None = None
    package_result: ProcessedSubtitlePackage | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class SubtitleAcquireResult:
    success: bool
    candidate: MediaCandidate
    selected_result: SubtitleSearchResult | None
    media_dir: Path
    raw_dir: Path
    extracted_dir: Path
    download_result: SubtitleDownloadResult | None = None
    package_result: ProcessedSubtitlePackage | None = None
    error_message: str | None = None
    attempts: tuple[SubtitleAcquireAttempt, ...] = ()

    @property
    def subtitle_files(self) -> list[Path]:
        if self.package_result is None:
            return []
        return self.package_result.subtitle_files


class SubtitleAcquirePipeline:
    """字幕获取闭环。

    职责：
    - 从搜索结果中选择最合适的字幕；
    - 调用 DownloadManager 下载原始字幕包；
    - 调用 PackageProcessor 解包并筛选字幕文件；
    - 返回结构化结果。

    不负责：
    - provider 搜索；
    - SubDL / Assrt 专属 URL 解析；
    - 字幕内容清洗；
    - AI_SUBTITLE_LIBRARY 入库；
    - 批量并发调度。
    """

    def __init__(
        self,
        *,
        download_manager: SubtitleDownloadManager | None = None,
        package_processor: SubtitlePackageProcessor | None = None,
        min_score: float = 0.0,
        preferred_languages: Sequence[str] | None = DEFAULT_PREFERRED_LANGUAGES,
    ) -> None:
        self.download_manager = download_manager or SubtitleDownloadManager()
        self.package_processor = package_processor or SubtitlePackageProcessor()
        self.min_score = min_score
        self.preferred_languages = (
            tuple(preferred_languages) if preferred_languages is not None else None
        )

    async def close(self) -> None:
        await self.download_manager.close()

    async def acquire(
        self,
        candidate: MediaCandidate,
        results: Sequence[SubtitleSearchResult],
        output_root: str | Path,
        *,
        min_score: float | None = None,
        max_size_bytes: int | None = DEFAULT_MAX_SUBTITLE_PACKAGE_BYTES,
        overwrite: bool = False,
    ) -> SubtitleAcquireResult:
        media_dir = Path(output_root) / "subtitles" / "inbox" / _media_key(candidate)
        raw_dir = media_dir / "raw"
        extracted_dir = media_dir / "extracted"

        ranked_results = rank_results(
            results,
            min_score=self.min_score if min_score is None else min_score,
            preferred_languages=self.preferred_languages,
        )

        if not ranked_results:
            return SubtitleAcquireResult(
                success=False,
                candidate=candidate,
                selected_result=None,
                media_dir=media_dir,
                raw_dir=raw_dir,
                extracted_dir=extracted_dir,
                error_message="没有可下载的字幕结果。",
            )

        attempts: list[SubtitleAcquireAttempt] = []
        last_error_message: str | None = None

        for selected in ranked_results:
            download_result = await self.download_manager.download(
                selected,
                raw_dir,
                max_size_bytes=max_size_bytes,
                overwrite=overwrite,
                auto_rename=True,
            )

            if not download_result.success or download_result.path is None:
                last_error_message = download_result.error_message or "字幕下载失败。"
                attempts.append(
                    SubtitleAcquireAttempt(
                        selected_result=selected,
                        download_result=download_result,
                        error_message=last_error_message,
                    )
                )
                continue

            package_result = self.package_processor.process(
                download_result.path,
                extracted_dir,
                overwrite=overwrite,
            )

            if not package_result.success:
                last_error_message = package_result.error_message or "字幕包处理失败。"
                attempts.append(
                    SubtitleAcquireAttempt(
                        selected_result=selected,
                        download_result=download_result,
                        package_result=package_result,
                        error_message=last_error_message,
                    )
                )
                continue

            attempts.append(
                SubtitleAcquireAttempt(
                    selected_result=selected,
                    download_result=download_result,
                    package_result=package_result,
                )
            )

            return SubtitleAcquireResult(
                success=True,
                candidate=candidate,
                selected_result=selected,
                media_dir=media_dir,
                raw_dir=raw_dir,
                extracted_dir=extracted_dir,
                download_result=download_result,
                package_result=package_result,
                attempts=tuple(attempts),
            )

        last_attempt = attempts[-1]

        return SubtitleAcquireResult(
            success=False,
            candidate=candidate,
            selected_result=last_attempt.selected_result,
            media_dir=media_dir,
            raw_dir=raw_dir,
            extracted_dir=extracted_dir,
            download_result=last_attempt.download_result,
            package_result=last_attempt.package_result,
            error_message=last_error_message or "所有字幕结果均获取失败。",
            attempts=tuple(attempts),
        )


def rank_results(
    results: Sequence[SubtitleSearchResult],
    *,
    min_score: float = 0.0,
    preferred_languages: Sequence[str] | None = DEFAULT_PREFERRED_LANGUAGES,
) -> list[SubtitleSearchResult]:
    downloadable = [
        result for result in results if result.download_url and result.score >= min_score
    ]

    if not downloadable:
        return []

    if not preferred_languages:
        return sorted(downloadable, key=lambda item: item.score, reverse=True)

    return sorted(
        downloadable,
        key=lambda item: (
            0 if _matches_preferred_language(item, preferred_languages) else 1,
            -item.score,
        ),
    )


def select_best_result(
    results: Sequence[SubtitleSearchResult],
    *,
    min_score: float = 0.0,
    preferred_languages: Sequence[str] | None = DEFAULT_PREFERRED_LANGUAGES,
) -> SubtitleSearchResult | None:
    ranked = rank_results(
        results,
        min_score=min_score,
        preferred_languages=preferred_languages,
    )
    if not ranked:
        return None
    return ranked[0]


def _media_key(candidate: MediaCandidate) -> str:
    return f"{candidate.media_type}_{candidate.tmdb_id}"
