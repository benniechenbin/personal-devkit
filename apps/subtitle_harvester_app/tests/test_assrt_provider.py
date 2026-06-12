from __future__ import annotations

import httpx
import pytest

from subtitle_harvester_app.providers.assrt.client import AssrtApiClient, AssrtQuotaExceeded
from subtitle_harvester_app.providers.assrt.provider import AssrtApiProvider
from subtitle_harvester_app.schema import MediaCandidate


def _candidate() -> MediaCandidate:
    return MediaCandidate(
        media_type="movie",
        tmdb_id=980477,
        imdb_id="tt0000001",
        title="哪吒之魔童闹海",
        original_title="哪吒之魔童闹海",
        year=2025,
        release_date="2025-01-29",
        original_language="zh",
        overview=None,
        aliases=["Ne Zha 2"],
    )


def test_assrt_provider_searches_detail_and_returns_downloadable_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        assert "token" not in request.url.params
        assert request.headers["authorization"] == "Bearer test-token"
        assert request.headers["accept"] == "application/json"

        if path == "/v1/sub/search":
            assert request.url.params.get("q") == "哪吒之魔童闹海"
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "sub": {
                        "result": "succeed",
                        "subs": [
                            {
                                "id": 123456,
                                "native_name": "哪吒之魔童闹海 / Ne Zha 2",
                                "videoname": "Ne.Zha.2.2025.1080p.WEB-DL",
                                "subtype": "Subrip(srt)",
                                "vote_score": 10,
                                "lang": {"desc": "简体中文"},
                            }
                        ],
                    },
                },
                request=request,
            )

        if path == "/v1/sub/detail":
            assert request.url.params.get("id") == "123456"
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "sub": {
                        "result": "succeed",
                        "subs": [
                            {
                                "id": 123456,
                                "filename": "Ne.Zha.2.2025.zip",
                                "native_name": "哪吒之魔童闹海 / Ne Zha 2",
                                "title": "哪吒之魔童闹海 Ne Zha 2 2025",
                                "videoname": "Ne.Zha.2.2025.1080p.WEB-DL",
                                "url": "https://file.assrt.net/download/123456/demo.zip",
                                "down_count": 200,
                                "vote_score": 10,
                                "lang": {"desc": "简体中文"},
                                "filelist": [
                                    {
                                        "url": "https://file.assrt.net/onthefly/123456/demo.srt",
                                        "f": "Ne.Zha.2.2025.zh.srt",
                                        "s": "52KB",
                                    }
                                ],
                            }
                        ],
                    },
                },
                request=request,
            )

        return httpx.Response(404, request=request)

    http_client = httpx.Client(
        base_url="https://api.assrt.net",
        transport=httpx.MockTransport(handler),
    )
    client = AssrtApiClient(token="test-token", client=http_client)
    provider = AssrtApiProvider(
        token="test-token",
        client=client,
        max_detail_results=3,
    )

    try:
        results = provider.search(_candidate())
    finally:
        provider.close()

    assert len(results) == 1

    result = results[0]
    assert result.provider == "assrt"
    assert result.media_type == "movie"
    assert result.tmdb_id == 980477
    assert result.imdb_id == "tt0000001"
    assert result.language == "简体中文"
    assert result.file_name == "Ne.Zha.2.2025.zh.srt"
    assert result.download_url == "https://file.assrt.net/onthefly/123456/demo.srt"
    assert result.source_id == "123456:file:0"
    assert result.score > 0


def test_assrt_quota_exceeded_is_not_swallowed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(509, request=request)

    http_client = httpx.Client(
        base_url="https://api.assrt.net",
        transport=httpx.MockTransport(handler),
    )
    client = AssrtApiClient(token="test-token", client=http_client)
    provider = AssrtApiProvider(token="test-token", client=client)

    try:
        with pytest.raises(AssrtQuotaExceeded):
            provider.search(_candidate())
    finally:
        provider.close()
