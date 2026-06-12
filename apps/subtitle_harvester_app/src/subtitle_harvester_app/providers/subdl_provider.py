from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

import httpx
from loguru import logger

from subtitle_harvester_app.providers.base import SubtitleSearchResult
from subtitle_harvester_app.schema import MediaCandidate


class SubDLProvider:
    name = "subdl"

    API_BASE = "https://api.subdl.com/api/v1"
    DOWNLOAD_BASE = "https://dl.subdl.com"

    def __init__(
        self,
        *,
        api_key: str,
        languages: str = "ZH,ZH-CN,EN",
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.languages = languages
        self.client = httpx.Client(
            base_url=self.API_BASE,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

    def close(self) -> None:
        self.client.close()

    def search(self, candidate: MediaCandidate) -> list[SubtitleSearchResult]:
        params: dict[str, Any] = {
            "api_key": self.api_key,
            "type": candidate.media_type,
            "languages": self.languages,
            "year": candidate.year,
            "subs_per_page": 10,
            "unpack": 1,
            "releases": 1,
        }

        # 优先 ID 搜索，其次片名搜索
        if candidate.imdb_id:
            params["imdb_id"] = candidate.imdb_id
        elif candidate.tmdb_id:
            params["tmdb_id"] = candidate.tmdb_id
        else:
            params["film_name"] = candidate.original_title or candidate.title

        response = self.client.get("/subtitles", params=params)
        response.raise_for_status()
        payload = response.json()

        if not payload.get("status"):
            logger.debug(
                "SubDL 返回空状态：title={} tmdb_id={} imdb_id={} payload={}",
                candidate.title,
                candidate.tmdb_id,
                candidate.imdb_id,
                payload,
            )
            return []

        return self._parse_results(candidate, payload)

    def _parse_results(
        self,
        candidate: MediaCandidate,
        payload: dict[str, Any],
    ) -> list[SubtitleSearchResult]:
        results: list[SubtitleSearchResult] = []

        for item in payload.get("subtitles", []):
            # 整季解包文件
            unpack_files = item.get("unpack_files") or []
            if unpack_files:
                for unpacked in unpack_files:
                    raw = {**item, **unpacked}
                    results.append(
                        SubtitleSearchResult(
                            provider=self.name,
                            media_type=candidate.media_type,
                            tmdb_id=candidate.tmdb_id,
                            imdb_id=candidate.imdb_id,
                            title=candidate.title,
                            year=candidate.year,
                            language=unpacked.get("language") or "",
                            release_name=unpacked.get("release_name"),
                            file_name=unpacked.get("name"),
                            download_url=_resolve_download_url(unpacked.get("url")),
                            source_id=unpacked.get("file_n_id"),
                            season=unpacked.get("season"),
                            episode=unpacked.get("episode"),
                            score=_score_subdl_result(candidate, raw),
                            raw=raw,
                        )
                    )
                continue

            results.append(
                SubtitleSearchResult(
                    provider=self.name,
                    media_type=candidate.media_type,
                    tmdb_id=candidate.tmdb_id,
                    imdb_id=candidate.imdb_id,
                    title=candidate.title,
                    year=candidate.year,
                    language=item.get("language") or "",
                    release_name=item.get("release_name"),
                    file_name=item.get("name"),
                    download_url=_resolve_download_url(item.get("url")),
                    season=item.get("season"),
                    episode=item.get("episode"),
                    score=_score_subdl_result(candidate, item),
                    raw=item,
                )
            )

        return results


def _resolve_download_url(value: str | None) -> str | None:
    if not value:
        return None
    if value.startswith("http"):
        return value
    return urljoin(SubDLProvider.DOWNLOAD_BASE, value)


def _score_subdl_result(candidate: MediaCandidate, item: dict[str, Any]) -> float:
    score = 0.0

    if item.get("url"):
        score += 30.0
    if item.get("language"):
        score += 10.0
    if item.get("file_n_id") or item.get("id"):
        score += 5.0

    title_terms = _text_terms(candidate.title, candidate.original_title, *candidate.aliases)
    release_terms = _text_terms(item.get("release_name"), item.get("name"))
    if title_terms and release_terms:
        overlap = title_terms & release_terms
        score += min(25.0, len(overlap) * 8.0)

    if candidate.year and str(candidate.year) in " ".join(
        str(item.get(field) or "") for field in ("release_name", "name")
    ):
        score += 5.0

    score += min(10.0, _numeric_field(item, "downloads", "download_count", "downloaded") / 20.0)
    score += min(10.0, _numeric_field(item, "rating", "score", "votes"))

    if _looks_hearing_impaired(item.get("release_name"), item.get("name")):
        score -= 5.0

    return max(score, 0.0)


def _text_terms(*values: str | None) -> set[str]:
    terms: set[str] = set()
    for value in values:
        if not value:
            continue
        for token in re.split(r"[^a-z0-9\u4e00-\u9fff]+", value.lower()):
            if len(token) >= 2:
                terms.add(token)
    return terms


def _numeric_field(item: dict[str, Any], *field_names: str) -> float:
    for field_name in field_names:
        value = item.get(field_name)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return 0.0


def _looks_hearing_impaired(*values: str | None) -> bool:
    text = " ".join(value.lower() for value in values if value)
    if "hearing impaired" in text:
        return True
    tokens = {token for token in re.split(r"[^a-z0-9]+", text) if token}
    return bool(tokens & {"hi", "sdh"})
