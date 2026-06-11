import json
from pathlib import Path

from subtitle_harvester_app import cli
from subtitle_harvester_app.config.settings import Settings
from subtitle_harvester_app.schema import MediaCandidate


def test_parse_args_defaults_to_all_media_for_current_year() -> None:
    args = cli.parse_args([])

    assert args.media_type == "all"
    assert args.month is None
    assert args.max_pages is None


def _demo_candidate(tmdb_id: int = 1) -> MediaCandidate:
    return MediaCandidate(
        media_type="movie",
        tmdb_id=tmdb_id,
        imdb_id=f"tt{tmdb_id:07d}",
        title="Demo",
        original_title="Demo",
        year=2026,
        release_date="2026-06-01",
        original_language="en",
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
    ) -> list[MediaCandidate]:
        assert self.api_key == "test-api-key"
        assert year == 2026
        assert month == 6
        assert tuple(media_types) == ("movie",)
        assert max_pages == 2

        return [_demo_candidate(tmdb_id=1)]

    def close(self) -> None:
        self.closed = True


def _patch_cli_dependencies(monkeypatch, tmp_path: Path) -> None:
    settings = Settings(
        app_env="test",
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "output",
        tmdb_api_key="test-api-key",
        tmdb_max_pages=7,
    )

    monkeypatch.setattr(cli, "get_settings", lambda: settings)
    monkeypatch.setattr(cli, "TmdbDiscoveryClient", FakeTmdbDiscoveryClient)
    monkeypatch.setattr(cli, "utc_now_iso", lambda: "2026-06-11T00:00:00+00:00")


def test_cli_writes_snapshot_batch_and_state_first_run(monkeypatch, tmp_path: Path) -> None:
    _patch_cli_dependencies(monkeypatch, tmp_path)
    monkeypatch.setattr(cli, "_run_id", lambda: "20260611_000001")

    cli.main(
        [
            "--year",
            "2026",
            "--month",
            "6",
            "--media-type",
            "movie",
            "--max-pages",
            "2",
        ]
    )

    output_dir = tmp_path / "output"

    snapshot_files = list((output_dir / "snapshots").glob("*.snapshot.json"))
    batch_files = list((output_dir / "batches").glob("*.batch.json"))
    state_path = output_dir / "state" / "seen_media_candidates.json"

    assert len(snapshot_files) == 1
    assert len(batch_files) == 1
    assert state_path.exists()

    snapshot_payload = json.loads(snapshot_files[0].read_text(encoding="utf-8"))
    batch_payload = json.loads(batch_files[0].read_text(encoding="utf-8"))
    state_payload = json.loads(state_path.read_text(encoding="utf-8"))

    assert snapshot_payload["metadata"]["kind"] == "snapshot"
    assert snapshot_payload["count"] == 1
    assert snapshot_payload["items"][0]["tmdb_id"] == 1

    assert batch_payload["metadata"]["kind"] == "batch"
    assert batch_payload["count"] == 1
    assert batch_payload["items"][0]["tmdb_id"] == 1

    assert "movie:1" in state_payload["discovered"]
    assert state_payload["discovered"]["movie:1"]["title"] == "Demo"

    assert (output_dir / "latest" / "latest_snapshot.json").exists()
    assert (output_dir / "latest" / "latest_batch.json").exists()


def test_cli_second_run_writes_empty_batch_for_seen_candidate(
    monkeypatch,
    tmp_path: Path,
) -> None:
    _patch_cli_dependencies(monkeypatch, tmp_path)

    run_ids = iter(["20260611_000001", "20260611_000002"])
    monkeypatch.setattr(cli, "_run_id", lambda: next(run_ids))

    args = [
        "--year",
        "2026",
        "--month",
        "6",
        "--media-type",
        "movie",
        "--max-pages",
        "2",
    ]

    cli.main(args)
    cli.main(args)

    output_dir = tmp_path / "output"
    batch_files = sorted((output_dir / "batches").glob("*.batch.json"))
    snapshot_files = sorted((output_dir / "snapshots").glob("*.snapshot.json"))

    assert len(snapshot_files) == 2
    assert len(batch_files) == 2

    first_batch = json.loads(batch_files[0].read_text(encoding="utf-8"))
    second_batch = json.loads(batch_files[1].read_text(encoding="utf-8"))

    assert first_batch["count"] == 1
    assert first_batch["items"][0]["tmdb_id"] == 1

    assert second_batch["count"] == 0
    assert second_batch["items"] == []

    state_path = output_dir / "state" / "seen_media_candidates.json"
    state_payload = json.loads(state_path.read_text(encoding="utf-8"))

    assert "movie:1" in state_payload["discovered"]
    assert state_payload["discovered"]["movie:1"]["first_seen_at"] == "2026-06-11T00:00:00+00:00"
    assert state_payload["discovered"]["movie:1"]["last_seen_at"] == "2026-06-11T00:00:00+00:00"


def test_parse_args_accepts_tmdb_origin_filters() -> None:
    args = cli.parse_args(
        [
            "--origin-country",
            "CN",
            "--original-language",
            "zh",
        ]
    )

    assert args.origin_country == "CN"
    assert args.original_language == "zh"
