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


def test_cli_writes_candidates_without_live_tmdb_call(monkeypatch, tmp_path: Path) -> None:
    output_path = tmp_path / "candidates.json"
    settings = Settings(
        app_env="test",
        log_dir=tmp_path / "logs",
        output_dir=tmp_path / "output",
        tmdb_api_key="test-api-key",
        tmdb_max_pages=7,
    )

    class FakeTmdbDiscoveryClient:
        def __init__(self, *, api_key: str, language: str, region: str) -> None:
            self.api_key = api_key
            self.language = language
            self.region = region
            self.closed = False

        def discover(self, *, year: int, month: int | None, media_types, max_pages: int):
            assert self.api_key == "test-api-key"
            assert year == 2026
            assert month == 6
            assert tuple(media_types) == ("movie",)
            assert max_pages == 2
            return [
                MediaCandidate(
                    media_type="movie",
                    tmdb_id=1,
                    imdb_id="tt0000001",
                    title="Demo",
                    original_title="Demo",
                    year=2026,
                    release_date="2026-06-01",
                    original_language="en",
                    overview=None,
                    aliases=["Demo"],
                )
            ]

        def close(self) -> None:
            self.closed = True

    monkeypatch.setattr(cli, "get_settings", lambda: settings)
    monkeypatch.setattr(cli, "TmdbDiscoveryClient", FakeTmdbDiscoveryClient)

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
            "--output",
            str(output_path),
        ]
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["count"] == 1
    assert payload["items"][0]["title"] == "Demo"
