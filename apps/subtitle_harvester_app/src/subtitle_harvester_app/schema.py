from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

MediaType = Literal["movie", "tv"]


@dataclass(frozen=True)
class MediaCandidate:
    media_type: MediaType
    tmdb_id: int
    imdb_id: str | None
    title: str
    original_title: str
    year: int | None
    release_date: str | None
    original_language: str | None
    overview: str | None
    aliases: list[str]
    source: str = "tmdb"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
