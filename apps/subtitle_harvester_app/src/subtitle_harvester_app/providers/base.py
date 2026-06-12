from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol

from subtitle_harvester_app.schema import MediaCandidate


@dataclass(frozen=True)
class SubtitleSearchResult:
    provider: str
    media_type: str
    tmdb_id: int | None
    imdb_id: str | None
    title: str
    year: int | None
    language: str
    release_name: str | None
    file_name: str | None
    download_url: str | None
    source_id: str | None = None
    season: int | None = None
    episode: int | None = None
    score: float = 0.0
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SubtitleProvider(Protocol):
    name: str

    def search(self, candidate: MediaCandidate) -> list[SubtitleSearchResult]: ...
