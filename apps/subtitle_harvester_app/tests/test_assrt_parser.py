from __future__ import annotations

from subtitle_harvester_app.providers.assrt.parser import parse_assrt_detail_results
from subtitle_harvester_app.schema import MediaCandidate


def test_assrt_parser_filters_irrelevant_detail_results() -> None:
    payload = {
        "status": 0,
        "sub": {
            "subs": [
                {
                    "id": 663583,
                    "filename": "Hijack.2023.S01E01.chs.srt",
                    "native_name": "Hijack 2023",
                    "videoname": "Hijack.2023.S01E01.1080p",
                    "lang": {"desc": "英 简 繁"},
                    "filelist": [
                        {
                            "url": "https://file.assrt.net/onthefly/663583/hijack.srt",
                            "f": "Hijack.2023.S01E01.chs.srt",
                        }
                    ],
                }
            ]
        },
    }

    candidate = MediaCandidate(
        media_type="movie",
        tmdb_id=123,
        imdb_id=None,
        title="森中有林",
        original_title="森中有林",
        year=2026,
        release_date="2026-01-01",
        original_language="zh",
        overview=None,
        aliases=[],
    )

    results = parse_assrt_detail_results(
        candidate=candidate,
        detail_payload=payload,
        search_item={"id": 663583, "native_name": "Hijack 2023"},
    )

    assert results == []
