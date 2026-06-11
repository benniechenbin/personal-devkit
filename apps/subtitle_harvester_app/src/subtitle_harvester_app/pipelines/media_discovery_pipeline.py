from __future__ import annotations

import shutil
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from subtitle_harvester_app.config.settings import Settings
from subtitle_harvester_app.discovery.tmdb_discovery import TmdbDiscoveryClient
from subtitle_harvester_app.outputs.json_writer import write_candidates_json
from subtitle_harvester_app.schema import MediaType
from subtitle_harvester_app.state.discovery_state import (
    load_seen_state,
    save_seen_state,
    split_new_candidates,
    utc_now_iso,
)


@dataclass(frozen=True)
class MediaDiscoveryRequest:
    year: int
    month: int | None
    media_type_label: str
    media_types: Sequence[MediaType]
    max_pages: int
    output_path: Path | None
    update_state: bool
    origin_country: str | None = None
    original_language: str | None = None
    sort_by: str | None = None
    min_vote_count: int | None = None
    min_runtime: int | None = None


@dataclass(frozen=True)
class MediaDiscoveryResult:
    snapshot_path: Path
    batch_path: Path
    state_path: Path
    total_candidates: int
    new_candidates: int
    state_updated: bool


def run_media_discovery(
    *,
    settings: Settings,
    request: MediaDiscoveryRequest,
    run_id: str,
) -> MediaDiscoveryResult:
    discovered_at = utc_now_iso()

    output_root = settings.resolved_output_dir
    snapshot_dir = output_root / "snapshots"
    batch_dir = output_root / "batches"
    latest_dir = output_root / "latest"
    state_path = output_root / "state" / "seen_media_candidates.json"

    period = _period_part(request.year, request.month)

    snapshot_path = (
        snapshot_dir
        / f"media_candidates_{period}_{request.media_type_label}_{run_id}.snapshot.json"
    )
    batch_path = request.output_path or (
        batch_dir / f"media_candidates_{period}_{request.media_type_label}_{run_id}.batch.json"
    )

    if settings.tmdb_api_key is None:
        raise RuntimeError("环境变量或 .env 中缺少 TMDB_API_KEY。")

    api_key = settings.tmdb_api_key.get_secret_value().strip()
    client = TmdbDiscoveryClient(
        api_key=api_key,
        language=settings.tmdb_language,
        region=settings.tmdb_region,
    )

    try:
        candidates = client.discover(
            year=request.year,
            month=request.month,
            media_types=request.media_types,
            max_pages=request.max_pages,
            origin_country=request.origin_country,
            original_language=request.original_language,
            sort_by=request.sort_by,
            min_vote_count=request.min_vote_count,
            min_runtime=request.min_runtime,
        )
    finally:
        client.close()

    state = load_seen_state(state_path)
    new_candidates, updated_state = split_new_candidates(
        candidates,
        state,
        now=discovered_at,
    )

    common_metadata = {
        "run_id": run_id,
        "discovered_at": discovered_at,
        "source": "tmdb",
        "year": request.year,
        "month": request.month,
        "media_type": request.media_type_label,
        "max_pages": request.max_pages,
        "origin_country": request.origin_country,
        "original_language": request.original_language,
        "sort_by": request.sort_by,
        "min_vote_count": request.min_vote_count,
        "min_runtime": request.min_runtime,
        "total_candidates": len(candidates),
        "new_candidates": len(new_candidates),
        "state_path": str(state_path),
    }

    write_candidates_json(
        candidates,
        snapshot_path,
        metadata={**common_metadata, "kind": "snapshot"},
    )

    write_candidates_json(
        new_candidates,
        batch_path,
        metadata={**common_metadata, "kind": "batch"},
    )

    latest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(snapshot_path, latest_dir / "latest_snapshot.json")
    shutil.copyfile(batch_path, latest_dir / "latest_batch.json")

    if request.update_state:
        save_seen_state(state_path, updated_state)

    return MediaDiscoveryResult(
        snapshot_path=snapshot_path,
        batch_path=batch_path,
        state_path=state_path,
        total_candidates=len(candidates),
        new_candidates=len(new_candidates),
        state_updated=request.update_state,
    )


def _period_part(year: int, month: int | None) -> str:
    return f"{year}_{month:02d}" if month else str(year)
