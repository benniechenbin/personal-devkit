from __future__ import annotations

import argparse

from subtitle_harvester_app.config.settings import get_settings
from subtitle_harvester_app.core.bootstrap import init_workspace
from subtitle_harvester_app.pipelines.media_discovery_pipeline import (
    MediaDiscoveryRequest,
    run_media_discovery,
)
from subtitle_harvester_app.schema import MediaType


def run_discover_command(
    args: argparse.Namespace,
    *,
    run_id: str,
) -> None:
    settings = init_workspace(get_settings(), require_tmdb=True)

    request = MediaDiscoveryRequest(
        year=args.year,
        month=args.month,
        media_type_label=args.media_type,
        media_types=_media_types(args.media_type),
        max_pages=args.max_pages or settings.tmdb_max_pages,
        output_path=args.output,
        update_state=not args.no_update_state,
        origin_country=args.origin_country,
        original_language=args.original_language,
        sort_by=args.sort_by,
        min_vote_count=args.min_vote_count,
        min_runtime=args.min_runtime,
    )

    result = run_media_discovery(
        settings=settings,
        request=request,
        run_id=run_id,
    )

    print(f"已生成快照：{result.snapshot_path}")
    print(f"已生成批次：{result.batch_path}")
    print(f"候选总数：{result.total_candidates}")
    print(f"新增候选数：{result.new_candidates}")

    if result.state_updated:
        print(f"已更新状态：{result.state_path}")
    else:
        print("已使用 --no-update-state，状态文件未更新。")


def _media_types(media_type: str) -> tuple[MediaType, ...]:
    if media_type == "all":
        return ("movie", "tv")
    if media_type == "movie":
        return ("movie",)
    if media_type == "tv":
        return ("tv",)
    raise ValueError(f"Unsupported media_type: {media_type}")
