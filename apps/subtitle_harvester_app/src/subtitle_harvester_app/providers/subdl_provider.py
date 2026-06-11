from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx

from subtitle_harvester_app.providers.base import (
    DownloadResult,
    SubtitleSearchResult,
)
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
            return []

        return self._parse_results(candidate, payload)

    def download(self, result: SubtitleSearchResult, output_dir: Path) -> DownloadResult:
        if not result.download_url:
            return DownloadResult(
                provider=self.name,
                source_url="",
                local_path=output_dir,
                status="failed",
                error_message="download_url is empty",
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        source_url = (
            result.download_url
            if result.download_url.startswith("http")
            else urljoin(self.DOWNLOAD_BASE, result.download_url)
        )

        safe_name = result.file_name or f"{result.title}.{result.language}.zip"
        local_path = output_dir / _safe_filename(safe_name)

        try:
            response = httpx.get(source_url, timeout=60.0)
            response.raise_for_status()
            local_path.write_bytes(response.content)

            return DownloadResult(
                provider=self.name,
                source_url=source_url,
                local_path=local_path,
                status="success",
            )
        except Exception as exc:
            return DownloadResult(
                provider=self.name,
                source_url=source_url,
                local_path=local_path,
                status="failed",
                error_message=str(exc),
            )

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
                            download_url=unpacked.get("url"),
                            source_id=unpacked.get("file_n_id"),
                            season=unpacked.get("season"),
                            episode=unpacked.get("episode"),
                            raw=unpacked,
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
                    download_url=item.get("url"),
                    season=item.get("season"),
                    episode=item.get("episode"),
                    raw=item,
                )
            )

        return results


def _safe_filename(name: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")
    return name.strip() or "subtitle.zip"
