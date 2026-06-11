from __future__ import annotations

import json
from pathlib import Path

from subtitle_harvester_app.config.settings import Settings
from subtitle_harvester_app.pipelines import media_discovery_pipeline as pipeline
from subtitle_harvester_app.pipelines.media_discovery_pipeline import (
    MediaDiscoveryRequest,
    run_media_discovery,
)
from subtitle_harvester_app.schema import MediaCandidate


def _demo_candidate(tmdb_id: int = 1) -> MediaCandidate:
    return MediaCandidate(
        media_type="movie",
        tmdb_id=tmdb_id,
        imdb_id=f"tt{tmdb_id:07d}",
        title="Demo",
        original_title="Demo",
        year=2026,
        release_date="2026-06-01",
        original_language="zh",
        overview=None,
        aliases=["Demo"],
    )


class FakeTmdbDiscoveryClient:
    def __init__(self, *, api_key: str, language: str, region: str) -> None:
        self.api_key = api_key
        self.language = language
        self.region = region
        self.closed = False

    def discover(
        self,
        *,
        year: int,
        month: int | None,
        media_types,
        max_pages: int,
        origin_country: str | None = None,
        original_language: str | None = None,
        sort_by: str | None = None,
        min_vote_count: int | None = None,
        min_runtime: int | None = None,
    ) -> list[MediaCandidate]:
        assert self.api_key == "test-api-key"
        assert self.language == "zh-CN"
        assert self.region == "CN"

        assert year == 2026
        assert month == 6
        assert tuple(media_types) == ("movie",)
        assert max_pages == 2

        assert origin_country is None
        assert original_language == "zh"
        assert sort_by == "popularity.desc"
        assert min_vote_count == 5
        assert min_runtime == 60

        return [_demo_candidate(tmdb_id=1)]

    def close(self) -> None:
        self.closed = True


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        app_env="test",
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "output",
        tmdb_api_key="test-api-key",
        tmdb_language="zh-CN",
        tmdb_region="CN",
        tmdb_max_pages=7,
    )


def _request(*, update_state: bool = True) -> MediaDiscoveryRequest:
    return MediaDiscoveryRequest(
        year=2026,
        month=6,
        media_type_label="movie",
        media_types=("movie",),
        max_pages=2,
        output_path=None,
        update_state=update_state,
        origin_country=None,
        original_language="zh",
        sort_by="popularity.desc",
        min_vote_count=5,
        min_runtime=60,
    )


def test_run_media_discovery_writes_snapshot_batch_latest_and_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(pipeline, "TmdbDiscoveryClient", FakeTmdbDiscoveryClient)
    monkeypatch.setattr(
        pipeline,
        "utc_now_iso",
        lambda: "2026-06-11T00:00:00+00:00",
    )

    result = run_media_discovery(
        settings=_settings(tmp_path),
        request=_request(update_state=True),
        run_id="20260611_000001",
    )

    output_dir = tmp_path / "output"

    assert result.total_candidates == 1
    assert result.new_candidates == 1
    assert result.state_updated is True

    assert result.snapshot_path.exists()
    assert result.batch_path.exists()
    assert result.state_path.exists()

    assert result.snapshot_path.name == (
        "media_candidates_2026_06_movie_20260611_000001.snapshot.json"
    )
    assert result.batch_path.name == ("media_candidates_2026_06_movie_20260611_000001.batch.json")

    assert (output_dir / "latest" / "latest_snapshot.json").exists()
    assert (output_dir / "latest" / "latest_batch.json").exists()

    snapshot_payload = json.loads(result.snapshot_path.read_text(encoding="utf-8"))
    batch_payload = json.loads(result.batch_path.read_text(encoding="utf-8"))
    state_payload = json.loads(result.state_path.read_text(encoding="utf-8"))

    assert snapshot_payload["metadata"]["kind"] == "snapshot"
    assert snapshot_payload["metadata"]["source"] == "tmdb"
    assert snapshot_payload["metadata"]["year"] == 2026
    assert snapshot_payload["metadata"]["month"] == 6
    assert snapshot_payload["metadata"]["media_type"] == "movie"
    assert snapshot_payload["metadata"]["max_pages"] == 2
    assert snapshot_payload["metadata"]["original_language"] == "zh"
    assert snapshot_payload["metadata"]["sort_by"] == "popularity.desc"
    assert snapshot_payload["metadata"]["min_vote_count"] == 5
    assert snapshot_payload["metadata"]["min_runtime"] == 60

    assert snapshot_payload["count"] == 1
    assert snapshot_payload["items"][0]["tmdb_id"] == 1
    assert snapshot_payload["items"][0]["title"] == "Demo"

    assert batch_payload["metadata"]["kind"] == "batch"
    assert batch_payload["count"] == 1
    assert batch_payload["items"][0]["tmdb_id"] == 1

    assert "movie:1" in state_payload["discovered"]
    assert state_payload["discovered"]["movie:1"]["title"] == "Demo"


def test_run_media_discovery_writes_empty_batch_for_seen_candidate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(pipeline, "TmdbDiscoveryClient", FakeTmdbDiscoveryClient)
    monkeypatch.setattr(
        pipeline,
        "utc_now_iso",
        lambda: "2026-06-11T00:00:00+00:00",
    )

    settings = _settings(tmp_path)
    request = _request(update_state=True)

    first_result = run_media_discovery(
        settings=settings,
        request=request,
        run_id="20260611_000001",
    )
    second_result = run_media_discovery(
        settings=settings,
        request=request,
        run_id="20260611_000002",
    )

    assert first_result.total_candidates == 1
    assert first_result.new_candidates == 1

    assert second_result.total_candidates == 1
    assert second_result.new_candidates == 0
    assert second_result.state_updated is True

    first_batch_payload = json.loads(first_result.batch_path.read_text(encoding="utf-8"))
    second_batch_payload = json.loads(second_result.batch_path.read_text(encoding="utf-8"))
    second_snapshot_payload = json.loads(second_result.snapshot_path.read_text(encoding="utf-8"))

    assert first_batch_payload["count"] == 1
    assert first_batch_payload["items"][0]["tmdb_id"] == 1

    assert second_snapshot_payload["count"] == 1
    assert second_snapshot_payload["items"][0]["tmdb_id"] == 1

    assert second_batch_payload["count"] == 0
    assert second_batch_payload["items"] == []

    state_payload = json.loads(second_result.state_path.read_text(encoding="utf-8"))

    assert "movie:1" in state_payload["discovered"]
    assert state_payload["discovered"]["movie:1"]["first_seen_at"] == "2026-06-11T00:00:00+00:00"
    assert state_payload["discovered"]["movie:1"]["last_seen_at"] == "2026-06-11T00:00:00+00:00"
