from __future__ import annotations

import json
from pathlib import Path

from subtitle_harvester_app.providers.base import SubtitleSearchResult
from subtitle_harvester_app.routing.subtitle_router import SubtitleRouter
from subtitle_harvester_app.schema import MediaCandidate


def load_candidates(path: Path, *, limit: int | None = None) -> list[MediaCandidate]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", [])

    candidates = [
        MediaCandidate(**item) for item in items if item.get("imdb_id") or item.get("tmdb_id")
    ]

    return candidates[:limit] if limit else candidates


class SubtitleSearchPipeline:
    def __init__(self, router: SubtitleRouter) -> None:
        self.router = router

    def run(
        self,
        candidates_path: Path,
        *,
        limit: int | None = None,
    ) -> list[SubtitleSearchResult]:
        candidates = load_candidates(candidates_path, limit=limit)

        all_results: list[SubtitleSearchResult] = []
        for candidate in candidates:
            all_results.extend(self.router.search_all(candidate))

        return all_results
