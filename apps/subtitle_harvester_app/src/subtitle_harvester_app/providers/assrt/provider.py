from __future__ import annotations

from loguru import logger

from subtitle_harvester_app.providers.assrt.client import AssrtApiClient, AssrtQuotaExceeded
from subtitle_harvester_app.providers.assrt.parser import (
    build_assrt_queries,
    is_assrt_relevant,
    parse_assrt_detail_results,
    parse_assrt_search_subs,
)
from subtitle_harvester_app.providers.base import SubtitleSearchResult
from subtitle_harvester_app.schema import MediaCandidate


class AssrtApiProvider:
    name = "assrt"

    def __init__(
        self,
        *,
        token: str,
        client: AssrtApiClient | None = None,
        search_count: int = 10,
        max_detail_results: int = 5,
    ) -> None:
        self.client = client or AssrtApiClient(token=token)
        self.search_count = search_count
        self.max_detail_results = max_detail_results

    def close(self) -> None:
        self.client.close()

    def search(self, candidate: MediaCandidate) -> list[SubtitleSearchResult]:
        queries = build_assrt_queries(candidate)
        if not queries:
            return []

        results: list[SubtitleSearchResult] = []
        seen_ids: set[int] = set()

        for query in queries:
            try:
                payload = self.client.search(
                    query,
                    count=self.search_count,
                    position=0,
                    filelist=False,
                )
            except AssrtQuotaExceeded:
                raise
            except Exception as exc:
                logger.warning(
                    "Assrt 搜索失败：title={} query={} error={}",
                    candidate.title,
                    query,
                    exc,
                )
                continue

            search_items = parse_assrt_search_subs(payload)
            if not search_items:
                continue

            detail_count = 0

            for item in search_items:
                if detail_count >= self.max_detail_results:
                    break

                if not is_assrt_relevant(candidate, {"search": item}):
                    continue

                subtitle_id = _subtitle_id(item)
                if subtitle_id is None or subtitle_id in seen_ids:
                    continue

                seen_ids.add(subtitle_id)
                detail_count += 1

                try:
                    detail_payload = self.client.detail(subtitle_id)
                except AssrtQuotaExceeded:
                    raise
                except Exception as exc:
                    logger.warning(
                        "Assrt 详情获取失败：title={} subtitle_id={} error={}",
                        candidate.title,
                        subtitle_id,
                        exc,
                    )
                    continue

                results.extend(
                    parse_assrt_detail_results(
                        candidate=candidate,
                        detail_payload=detail_payload,
                        search_item=item,
                    )
                )

            if results:
                break

        return _dedupe_results(results)


def _subtitle_id(item: dict[str, object]) -> int | None:
    value = item.get("id")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _dedupe_results(
    results: list[SubtitleSearchResult],
) -> list[SubtitleSearchResult]:
    seen: set[tuple[str | None, str | None]] = set()
    deduped: list[SubtitleSearchResult] = []

    for result in results:
        key = (result.source_id, result.download_url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(result)

    return sorted(deduped, key=lambda item: item.score, reverse=True)
