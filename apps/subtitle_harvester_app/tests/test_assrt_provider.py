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


def test_assrt_client_raises_quota_exceeded_without_token_query() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "token" not in request.url.params
        assert request.headers["authorization"] == "Bearer test-token"
        return httpx.Response(509, request=request)

    http_client = httpx.Client(
        base_url="https://api.assrt.net",
        transport=httpx.MockTransport(handler),
    )
    client = AssrtApiClient(token="test-token", client=http_client)

    with pytest.raises(AssrtQuotaExceeded):
        client.search("哪吒之魔童闹海")

    client.close()


def test_assrt_provider_skips_irrelevant_search_items_before_detail() -> None:
    detail_calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path

        if path == "/v1/sub/search":
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "sub": {
                        "subs": [
                            {
                                "id": 1,
                                "native_name": "Hijack 2023",
                                "videoname": "Hijack.S01E01.1080p",
                                "lang": {"desc": "英 简 繁"},
                            },
                            {
                                "id": 2,
                                "native_name": "哪吒之魔童闹海 Ne Zha 2",
                                "videoname": "Ne.Zha.2.2025.1080p",
                                "lang": {"desc": "简体中文"},
                            },
                        ]
                    },
                },
                request=request,
            )

        if path == "/v1/sub/detail":
            subtitle_id = request.url.params.get("id")
            detail_calls.append(subtitle_id or "")

            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "sub": {
                        "subs": [
                            {
                                "id": int(subtitle_id or 0),
                                "filename": "Ne.Zha.2.2025.zip",
                                "native_name": "哪吒之魔童闹海 Ne Zha 2",
                                "videoname": "Ne.Zha.2.2025.1080p",
                                "lang": {"desc": "简体中文"},
                                "filelist": [
                                    {
                                        "url": "https://file.assrt.net/onthefly/2/demo.srt",
                                        "f": "Ne.Zha.2.2025.zh.srt",
                                    }
                                ],
                            }
                        ]
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
        max_detail_results=1,
    )

    try:
        results = provider.search(_candidate())
    finally:
        provider.close()

    assert detail_calls == ["2"]
    assert len(results) == 1
    assert results[0].source_id == "2:file:0"
    assert results[0].download_url == "https://file.assrt.net/onthefly/2/demo.srt"


def test_assrt_provider_limits_relevant_detail_requests() -> None:
    detail_calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path

        if path == "/v1/sub/search":
            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "sub": {
                        "subs": [
                            {
                                "id": 1,
                                "native_name": "哪吒之魔童闹海 版本1",
                                "videoname": "Ne.Zha.2.2025.A",
                                "lang": {"desc": "简体中文"},
                            },
                            {
                                "id": 2,
                                "native_name": "哪吒之魔童闹海 版本2",
                                "videoname": "Ne.Zha.2.2025.B",
                                "lang": {"desc": "简体中文"},
                            },
                            {
                                "id": 3,
                                "native_name": "哪吒之魔童闹海 版本3",
                                "videoname": "Ne.Zha.2.2025.C",
                                "lang": {"desc": "简体中文"},
                            },
                        ]
                    },
                },
                request=request,
            )

        if path == "/v1/sub/detail":
            subtitle_id = request.url.params.get("id") or ""
            detail_calls.append(subtitle_id)

            return httpx.Response(
                200,
                json={
                    "status": 0,
                    "sub": {
                        "subs": [
                            {
                                "id": int(subtitle_id),
                                "filename": f"Ne.Zha.2.{subtitle_id}.zip",
                                "native_name": "哪吒之魔童闹海",
                                "videoname": f"Ne.Zha.2.2025.{subtitle_id}",
                                "lang": {"desc": "简体中文"},
                                "filelist": [
                                    {
                                        "url": f"https://file.assrt.net/onthefly/{subtitle_id}/demo.srt",
                                        "f": f"Ne.Zha.2.2025.{subtitle_id}.zh.srt",
                                    }
                                ],
                            }
                        ]
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
        max_detail_results=2,
    )

    try:
        results = provider.search(_candidate())
    finally:
        provider.close()

    assert detail_calls == ["1", "2"]
    assert len(results) == 2
