from __future__ import annotations

from collections.abc import Iterable

from loguru import logger

from subtitle_harvester_app.providers.base import SubtitleProvider, SubtitleSearchResult
from subtitle_harvester_app.schema import MediaCandidate


class SubtitleRouter:
    def __init__(self, providers: Iterable[SubtitleProvider]) -> None:
        self.providers = list(providers)

    def search_all(self, candidate: MediaCandidate) -> list[SubtitleSearchResult]:
        results: list[SubtitleSearchResult] = []

        for provider in self.providers:
            try:
                logger.info(
                    "搜索字幕：provider={} title={} year={} imdb_id={} tmdb_id={}",
                    provider.name,
                    candidate.title,
                    candidate.year,
                    candidate.imdb_id,
                    candidate.tmdb_id,
                )
                results.extend(provider.search(candidate))
            except Exception as exc:
                logger.warning(
                    "字幕搜索失败：provider={} title={} error={}",
                    provider.name,
                    candidate.title,
                    exc,
                )

        return results
