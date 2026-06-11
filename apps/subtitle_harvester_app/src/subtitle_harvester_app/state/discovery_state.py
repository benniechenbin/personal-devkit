from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from subtitle_harvester_app.schema import MediaCandidate


@dataclass(frozen=True)
class CandidateStateEntry:
    first_seen_at: str
    last_seen_at: str
    media_type: str
    tmdb_id: int
    title: str
    original_title: str
    year: int | None
    release_date: str | None
    imdb_id: str | None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def candidate_key(candidate: MediaCandidate) -> str:
    return f"{candidate.media_type}:{candidate.tmdb_id}"


def load_seen_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "version": 1,
            "discovered": {},
        }

    payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    payload.setdefault("version", 1)
    payload.setdefault("discovered", {})
    return payload


def save_seen_state(path: Path, state: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def split_new_candidates(
    candidates: list[MediaCandidate],
    state: dict[str, Any],
    *,
    now: str | None = None,
) -> tuple[list[MediaCandidate], dict[str, Any]]:
    timestamp = now or utc_now_iso()
    discovered: dict[str, Any] = state.setdefault("discovered", {})

    new_candidates: list[MediaCandidate] = []

    for candidate in candidates:
        key = candidate_key(candidate)

        if key not in discovered:
            new_candidates.append(candidate)
            discovered[key] = asdict(
                CandidateStateEntry(
                    first_seen_at=timestamp,
                    last_seen_at=timestamp,
                    media_type=candidate.media_type,
                    tmdb_id=candidate.tmdb_id,
                    title=candidate.title,
                    original_title=candidate.original_title,
                    year=candidate.year,
                    release_date=candidate.release_date,
                    imdb_id=candidate.imdb_id,
                )
            )
        else:
            discovered[key]["last_seen_at"] = timestamp

    state["updated_at"] = timestamp
    return new_candidates, state
