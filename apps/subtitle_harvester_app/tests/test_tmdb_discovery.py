from __future__ import annotations

from typing import Any

from subtitle_harvester_app.discovery.tmdb_discovery import TmdbDiscoveryClient


def test_discover_movies_passes_origin_filters(monkeypatch) -> None:
    client = TmdbDiscoveryClient(api_key="test-api-key")
    captured: list[tuple[str, dict[str, Any] | None]] = []

    def fake_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        captured.append((path, params))
        return {"results": [], "total_pages": 1}

    monkeypatch.setattr(client, "_get", fake_get)

    try:
        client.discover_movies(
            start_date="2026-01-01",
            end_date="2026-12-31",
            max_pages=1,
            origin_country="CN",
            original_language="zh",
        )
    finally:
        client.close()

    assert len(captured) == 1
    assert captured[0][0] == "/discover/movie"
    assert captured[0][1] is not None
    assert captured[0][1]["with_origin_country"] == "CN"
    assert captured[0][1]["with_original_language"] == "zh"


def test_discover_tv_passes_origin_filters(monkeypatch) -> None:
    client = TmdbDiscoveryClient(api_key="test-api-key")
    captured: list[tuple[str, dict[str, Any] | None]] = []

    def fake_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        captured.append((path, params))
        return {"results": [], "total_pages": 1}

    monkeypatch.setattr(client, "_get", fake_get)

    try:
        client.discover_tv(
            start_date="2026-01-01",
            end_date="2026-12-31",
            max_pages=1,
            origin_country="CN",
            original_language="zh",
        )
    finally:
        client.close()

    assert len(captured) == 1
    assert captured[0][0] == "/discover/tv"
    assert captured[0][1] is not None
    assert captured[0][1]["with_origin_country"] == "CN"
    assert captured[0][1]["with_original_language"] == "zh"


def test_discover_defaults_do_not_add_origin_filters(monkeypatch) -> None:
    client = TmdbDiscoveryClient(api_key="test-api-key")
    captured: list[tuple[str, dict[str, Any] | None]] = []

    def fake_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        captured.append((path, params))
        return {"results": [], "total_pages": 1}

    monkeypatch.setattr(client, "_get", fake_get)

    try:
        client.discover_movies(
            start_date="2026-01-01",
            end_date="2026-12-31",
            max_pages=1,
        )
    finally:
        client.close()

    assert captured[0][1] is not None
    assert "with_origin_country" not in captured[0][1]
    assert "with_original_language" not in captured[0][1]
