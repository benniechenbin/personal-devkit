from __future__ import annotations

import calendar
from collections.abc import Iterable
from datetime import date
from typing import Any, Literal

import httpx

from subtitle_harvester_app.schema import MediaCandidate, MediaType


class TmdbDiscoveryClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(
        self,
        *,
        api_key: str,
        language: str = "zh-CN",
        region: str = "CN",
        timeout: float = 20.0,
    ) -> None:
        self.api_key = api_key
        self.language = language
        self.region = region
        self.client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=timeout,
            headers={
                "Accept": "application/json",
            },
        )

    def close(self) -> None:
        self.client.close()

    def discover(
        self,
        *,
        year: int,
        month: int | None = None,
        media_types: Iterable[MediaType] = ("movie", "tv"),
        max_pages: int = 3,
    ) -> list[MediaCandidate]:
        start_date, end_date = _date_range(year=year, month=month)
        candidates: list[MediaCandidate] = []

        for media_type in media_types:
            if media_type == "movie":
                candidates.extend(
                    self.discover_movies(
                        start_date=start_date,
                        end_date=end_date,
                        max_pages=max_pages,
                    )
                )
            elif media_type == "tv":
                candidates.extend(
                    self.discover_tv(
                        start_date=start_date,
                        end_date=end_date,
                        max_pages=max_pages,
                    )
                )
            else:
                raise ValueError(f"Unsupported media_type: {media_type}")

        return candidates

    def discover_movies(
        self,
        *,
        start_date: str,
        end_date: str,
        max_pages: int,
    ) -> list[MediaCandidate]:
        results: list[MediaCandidate] = []

        for page in range(1, max_pages + 1):
            payload = self._get(
                "/discover/movie",
                params={
                    "language": self.language,
                    "region": self.region,
                    "include_adult": "false",
                    "include_video": "false",
                    "sort_by": "primary_release_date.desc",
                    "primary_release_date.gte": start_date,
                    "primary_release_date.lte": end_date,
                    "page": page,
                },
            )

            for item in payload.get("results", []):
                results.append(self._movie_to_candidate(item))

            if page >= int(payload.get("total_pages", 1)):
                break

        return _dedupe_candidates(results)

    def discover_tv(
        self,
        *,
        start_date: str,
        end_date: str,
        max_pages: int,
    ) -> list[MediaCandidate]:
        results: list[MediaCandidate] = []

        for page in range(1, max_pages + 1):
            payload = self._get(
                "/discover/tv",
                params={
                    "language": self.language,
                    "include_adult": "false",
                    "include_null_first_air_dates": "false",
                    "sort_by": "first_air_date.desc",
                    "first_air_date.gte": start_date,
                    "first_air_date.lte": end_date,
                    "page": page,
                },
            )

            for item in payload.get("results", []):
                results.append(self._tv_to_candidate(item))

            if page >= int(payload.get("total_pages", 1)):
                break

        return _dedupe_candidates(results)

    def _movie_to_candidate(self, item: dict[str, Any]) -> MediaCandidate:
        tmdb_id = int(item["id"])
        external_ids = self._external_ids("movie", tmdb_id)

        title = item.get("title") or ""
        original_title = item.get("original_title") or title
        release_date = item.get("release_date") or None

        return MediaCandidate(
            media_type="movie",
            tmdb_id=tmdb_id,
            imdb_id=external_ids.get("imdb_id"),
            title=title,
            original_title=original_title,
            year=_extract_year(release_date),
            release_date=release_date,
            original_language=item.get("original_language"),
            overview=item.get("overview"),
            aliases=_build_aliases(title, original_title),
        )

    def _tv_to_candidate(self, item: dict[str, Any]) -> MediaCandidate:
        tmdb_id = int(item["id"])
        external_ids = self._external_ids("tv", tmdb_id)

        title = item.get("name") or ""
        original_title = item.get("original_name") or title
        first_air_date = item.get("first_air_date") or None

        return MediaCandidate(
            media_type="tv",
            tmdb_id=tmdb_id,
            imdb_id=external_ids.get("imdb_id"),
            title=title,
            original_title=original_title,
            year=_extract_year(first_air_date),
            release_date=first_air_date,
            original_language=item.get("original_language"),
            overview=item.get("overview"),
            aliases=_build_aliases(title, original_title),
        )

    def _external_ids(
        self,
        media_type: Literal["movie", "tv"],
        tmdb_id: int,
    ) -> dict[str, Any]:
        if media_type == "movie":
            return self._get(f"/movie/{tmdb_id}/external_ids")
        return self._get(f"/tv/{tmdb_id}/external_ids")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_params = dict(params or {})
        request_params["api_key"] = self.api_key

        try:
            response = self.client.get(path, params=request_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            body = exc.response.text[:300]
            if status == 401:
                raise RuntimeError(
                    "TMDb 认证失败：请确认 TMDB_API_KEY 是有效的 v3 API Key。"
                ) from exc
            raise RuntimeError(f"TMDb API 返回错误：HTTP {status}，{body}") from exc
        except httpx.ConnectTimeout as exc:
            raise RuntimeError("连接 TMDb 超时：请检查网络、代理或 TUN 模式。") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"TMDb API 请求失败：{exc}") from exc


def _date_range(*, year: int, month: int | None) -> tuple[str, str]:
    if month is None:
        return f"{year}-01-01", f"{year}-12-31"

    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")

    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}"


def _extract_year(raw_date: str | None) -> int | None:
    if not raw_date:
        return None
    try:
        return date.fromisoformat(raw_date).year
    except ValueError:
        return None


def _build_aliases(title: str, original_title: str) -> list[str]:
    aliases = []
    for value in [title, original_title]:
        value = value.strip()
        if value and value not in aliases:
            aliases.append(value)
    return aliases


def _dedupe_candidates(candidates: list[MediaCandidate]) -> list[MediaCandidate]:
    seen: set[tuple[str, int]] = set()
    deduped: list[MediaCandidate] = []

    for candidate in candidates:
        key = (candidate.media_type, candidate.tmdb_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)

    return deduped
