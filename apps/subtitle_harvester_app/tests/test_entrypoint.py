from __future__ import annotations

import argparse

from subtitle_harvester_app import cli


def test_parse_args_defaults_to_all_media_for_current_year() -> None:
    args = cli.parse_args([])

    assert args.media_type == "all"
    assert args.month is None
    assert args.max_pages is None
    assert args.output is None
    assert args.no_update_state is False


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


def test_parse_args_accepts_tmdb_discovery_tuning_filters() -> None:
    args = cli.parse_args(
        [
            "--sort-by",
            "popularity.desc",
            "--min-vote-count",
            "5",
            "--min-runtime",
            "60",
        ]
    )

    assert args.sort_by == "popularity.desc"
    assert args.min_vote_count == 5
    assert args.min_runtime == 60


def test_parse_args_rejects_invalid_month() -> None:
    try:
        cli.parse_args(["--month", "13"])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected argparse to reject invalid month")


def test_main_dispatches_discover_command(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_discover_command(args: argparse.Namespace, *, run_id: str) -> None:
        captured["args"] = args
        captured["run_id"] = run_id

    monkeypatch.setattr(cli, "run_discover_command", fake_run_discover_command)
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
            "--original-language",
            "zh",
            "--sort-by",
            "popularity.desc",
            "--no-update-state",
        ]
    )

    args = captured["args"]

    assert isinstance(args, argparse.Namespace)
    assert args.year == 2026
    assert args.month == 6
    assert args.media_type == "movie"
    assert args.max_pages == 2
    assert args.original_language == "zh"
    assert args.sort_by == "popularity.desc"
    assert args.no_update_state is True
    assert captured["run_id"] == "20260611_000001"
