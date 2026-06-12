from __future__ import annotations

import httpx

from subtitle_harvester_app.providers.subdl_provider import SubDLProvider
from subtitle_harvester_app.schema import MediaCandidate


def _candidate() -> MediaCandidate:
    return MediaCandidate(
        media_type="movie",
        tmdb_id=1,
        imdb_id="tt0000001",
        title="Demo Movie",
        original_title="Demo Movie",
        year=2026,
        release_date="2026-06-01",
        original_language="en",
        overview=None,
        aliases=[],
    )


def test_subdl_provider_scores_real_payload_results() -> None:
    provider = SubDLProvider(api_key="test")
    try:
        results = provider._parse_results(
            _candidate(),
            {
                "status": True,
                "subtitles": [
                    {
                        "language": "English",
                        "release_name": "Demo.Movie.2026.WEB-DL",
                        "name": "Demo.Movie.2026.English.zip",
                        "url": "/download/demo.zip",
                        "file_n_id": "sub-1",
                        "downloads": 120,
                        "rating": 8,
                    }
                ],
            },
        )
    finally:
        provider.close()

    assert len(results) == 1
    assert results[0].download_url == "https://dl.subdl.com/download/demo.zip"
    assert results[0].score > 0


def test_subdl_provider_scores_unpacked_files_with_parent_metadata() -> None:
    provider = SubDLProvider(api_key="test")
    try:
        results = provider._parse_results(
            _candidate(),
            {
                "status": True,
                "subtitles": [
                    {
                        "release_name": "Demo.Movie.2026",
                        "downloads": 80,
                        "unpack_files": [
                            {
                                "language": "Chinese",
                                "name": "Demo.Movie.2026.Chinese.srt",
                                "url": "/download/demo.srt",
                                "file_n_id": "sub-2",
                            }
                        ],
                    }
                ],
            },
        )
    finally:
        provider.close()

    assert len(results) == 1
    assert results[0].score > 0
    assert results[0].raw is not None
    assert results[0].raw["downloads"] == 80


def test_subdl_provider_search_sends_expected_id_params() -> None:
    captured_params: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_params
        captured_params = dict(request.url.params)
        return httpx.Response(
            200,
            json={
                "status": True,
                "subtitles": [
                    {
                        "language": "English",
                        "release_name": "Demo.Movie.2026",
                        "name": "Demo.Movie.2026.zip",
                        "url": "/download/demo.zip",
                    }
                ],
            },
            request=request,
        )

    provider = SubDLProvider(api_key="secret", languages="ZH,EN")
    provider.client = httpx.Client(
        base_url=provider.API_BASE,
        transport=httpx.MockTransport(handler),
    )

    try:
        results = provider.search(_candidate())
    finally:
        provider.close()

    assert captured_params["api_key"] == "secret"
    assert captured_params["type"] == "movie"
    assert captured_params["languages"] == "ZH,EN"
    assert captured_params["year"] == "2026"
    assert captured_params["imdb_id"] == "tt0000001"
    assert "tmdb_id" not in captured_params
    assert captured_params["unpack"] == "1"
    assert captured_params["releases"] == "1"
    assert len(results) == 1


def test_subdl_provider_search_falls_back_to_film_name_without_ids() -> None:
    captured_params: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_params
        captured_params = dict(request.url.params)
        return httpx.Response(
            200,
            json={"status": True, "subtitles": []},
            request=request,
        )

    candidate = MediaCandidate(
        media_type="movie",
        tmdb_id=0,
        imdb_id=None,
        title="Localized Title",
        original_title="Original Title",
        year=None,
        release_date=None,
        original_language=None,
        overview=None,
        aliases=[],
    )
    provider = SubDLProvider(api_key="secret")
    provider.client = httpx.Client(
        base_url=provider.API_BASE,
        transport=httpx.MockTransport(handler),
    )

    try:
        provider.search(candidate)
    finally:
        provider.close()

    assert captured_params["film_name"] == "Original Title"
    assert "imdb_id" not in captured_params
    assert "tmdb_id" not in captured_params
