from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from subtitle_harvester_app.providers.base import SubtitleSearchResult
from subtitle_harvester_app.schema import MediaCandidate


def build_assrt_queries(candidate: MediaCandidate) -> list[str]:
    """为 Assrt 搜索构造查询词。

    Assrt search 主要接收 q 字符串，不像 SubDL 那样直接支持 imdb_id/tmdb_id。
    所以这里优先使用中文标题、原始标题和别名。
    """
    values = [
        candidate.title,
        candidate.original_title,
        *candidate.aliases,
    ]

    queries: list[str] = []
    for value in values:
        query = (value or "").strip()
        if len(query) < 3:
            continue
        if query not in queries:
            queries.append(query)

    return queries


def parse_assrt_search_subs(payload: dict[str, Any]) -> list[dict[str, Any]]:
    sub = payload.get("sub")
    if not isinstance(sub, dict):
        return []

    subs = sub.get("subs")
    if not isinstance(subs, list):
        return []

    return [item for item in subs if isinstance(item, dict)]


def parse_assrt_detail_results(
    *,
    candidate: MediaCandidate,
    detail_payload: dict[str, Any],
    search_item: dict[str, Any] | None = None,
) -> list[SubtitleSearchResult]:
    sub = detail_payload.get("sub")
    if not isinstance(sub, dict):
        return []

    subs = sub.get("subs")
    if not isinstance(subs, list):
        return []

    results: list[SubtitleSearchResult] = []

    for item in subs:
        if not isinstance(item, dict):
            continue

        subtitle_id = _int_or_none(item.get("id")) or _int_or_none((search_item or {}).get("id"))
        language = _language_desc(item, search_item)
        release_name = _first_text(
            item.get("videoname"),
            item.get("title"),
            item.get("native_name"),
            (search_item or {}).get("videoname"),
            (search_item or {}).get("native_name"),
        )

        filelist = item.get("filelist")
        if isinstance(filelist, list) and filelist:
            for index, file_item in enumerate(filelist):
                if not isinstance(file_item, dict):
                    continue

                download_url = _first_text(file_item.get("url"))
                if not download_url:
                    continue

                file_name = _first_text(file_item.get("f"), item.get("filename"))
                raw = {
                    "search": search_item or {},
                    "detail": item,
                    "file": file_item,
                }

                if not is_assrt_relevant(candidate, raw):
                    continue

                results.append(
                    SubtitleSearchResult(
                        provider="assrt",
                        media_type=candidate.media_type,
                        tmdb_id=candidate.tmdb_id,
                        imdb_id=candidate.imdb_id,
                        title=candidate.title,
                        year=candidate.year,
                        language=language,
                        release_name=release_name,
                        file_name=file_name,
                        download_url=download_url,
                        source_id=(
                            f"{subtitle_id}:file:{index}" if subtitle_id is not None else None
                        ),
                        score=score_assrt_result(candidate, raw),
                        raw=raw,
                    )
                )

            continue

        download_url = _first_text(item.get("url"))
        if not download_url:
            continue

        raw = {
            "search": search_item or {},
            "detail": item,
        }

        if not is_assrt_relevant(candidate, raw):
            continue

        results.append(
            SubtitleSearchResult(
                provider="assrt",
                media_type=candidate.media_type,
                tmdb_id=candidate.tmdb_id,
                imdb_id=candidate.imdb_id,
                title=candidate.title,
                year=candidate.year,
                language=language,
                release_name=release_name,
                file_name=_first_text(item.get("filename")),
                download_url=download_url,
                source_id=str(subtitle_id) if subtitle_id is not None else None,
                score=score_assrt_result(candidate, raw),
                raw=raw,
            )
        )

    return results


def score_assrt_result(candidate: MediaCandidate, item: dict[str, Any]) -> float:
    text = " ".join(_flatten_text(item))
    terms = _text_terms(candidate.title, candidate.original_title, *candidate.aliases)

    score = 10.0

    if candidate.title and candidate.title in text:
        score += 45.0

    if candidate.original_title and candidate.original_title in text:
        score += 35.0

    overlap = terms & _text_terms(text)
    score += min(30.0, len(overlap) * 8.0)

    if candidate.year and str(candidate.year) in text:
        score += 8.0

    language = text.lower()
    if any(marker in language for marker in ("简", "繁", "中", "双语", "chs", "cht", "chinese")):
        score += 25.0

    score += min(10.0, _numeric_from_nested(item, "vote_score") / 10.0)
    score += min(10.0, _numeric_from_nested(item, "down_count") / 100.0)

    return max(score, 0.0)


def _language_desc(
    item: dict[str, Any],
    search_item: dict[str, Any] | None,
) -> str:
    for source in (item, search_item or {}):
        lang = source.get("lang")
        if isinstance(lang, dict):
            desc = lang.get("desc")
            if isinstance(desc, str) and desc.strip():
                return desc.strip()
    return ""


def _first_text(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _text_terms(*values: str | None) -> set[str]:
    terms: set[str] = set()
    for value in values:
        if not value:
            continue
        for token in re.split(r"[^a-z0-9\u4e00-\u9fff]+", value.lower()):
            if len(token) >= 2:
                terms.add(token)
    return terms


def _flatten_text(value: Any) -> list[str]:
    texts: list[str] = []

    if isinstance(value, str):
        texts.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            texts.extend(_flatten_text(item))
    elif isinstance(value, list):
        for item in value:
            texts.extend(_flatten_text(item))

    return texts


def _numeric_from_nested(value: Any, key: str) -> float:
    if isinstance(value, dict):
        raw = value.get(key)
        if raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                return 0.0
        for item in value.values():
            nested = _numeric_from_nested(item, key)
            if nested:
                return nested

    if isinstance(value, list):
        for item in value:
            nested = _numeric_from_nested(item, key)
            if nested:
                return nested

    return 0.0


def _normalize_match_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.lower())


def is_assrt_relevant(candidate: MediaCandidate, raw: Mapping[str, object]) -> bool:
    text = _normalize_match_text(" ".join(_flatten_text(raw)))

    names = [
        candidate.title,
        candidate.original_title,
        *candidate.aliases,
    ]

    for name in names:
        normalized_name = _normalize_match_text(name or "")
        if len(normalized_name) >= 3 and normalized_name in text:
            return True

    return False
