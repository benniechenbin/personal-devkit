from __future__ import annotations

import argparse
import shutil
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from subtitle_harvester_app.config.settings import get_settings
from subtitle_harvester_app.core.bootstrap import init_workspace
from subtitle_harvester_app.discovery.tmdb_discovery import TmdbDiscoveryClient
from subtitle_harvester_app.outputs.json_writer import write_candidates_json
from subtitle_harvester_app.schema import MediaType
from subtitle_harvester_app.state.discovery_state import (
    load_seen_state,
    save_seen_state,
    split_new_candidates,
    utc_now_iso,
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从 TMDb 抓取电影和剧集字幕候选，并写出增量 JSON 批次。",
    )
    parser.add_argument("--year", type=int, default=datetime.now().year)
    parser.add_argument("--month", type=_month, default=None)
    parser.add_argument(
        "--media-type",
        choices=["movie", "tv", "all"],
        default="all",
    )
    parser.add_argument("--max-pages", type=_positive_int, default=None)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="可选的批次输出路径；快照和状态文件仍使用配置中的输出目录。",
    )
    parser.add_argument(
        "--no-update-state",
        action="store_true",
        help="写出 snapshot 和 batch，但不更新 seen state，适合 dry-run 检查。",
    )
    parser.add_argument(
        "--origin-country",
        default=None,
        help="按原产国家/地区过滤 TMDb discovery，例如 CN。",
    )
    parser.add_argument(
        "--original-language",
        default=None,
        help="按原始语言过滤 TMDb discovery，例如 zh。",
    )
    return parser.parse_args(argv)


def _month(value: str) -> int:
    month = int(value)
    if month < 1 or month > 12:
        raise argparse.ArgumentTypeError("month 必须在 1 到 12 之间")
    return month


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("值必须大于等于 1")
    return parsed


def _run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _period_part(year: int, month: int | None) -> str:
    return f"{year}_{month:02d}" if month else str(year)


def _media_types(media_type: str) -> tuple[MediaType, ...]:
    if media_type == "all":
        return ("movie", "tv")
    return (media_type,)  # type: ignore[return-value]


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    settings = init_workspace(get_settings(), require_tmdb=True)

    media_types = _media_types(args.media_type)
    period = _period_part(args.year, args.month)
    run_id = _run_id()
    discovered_at = utc_now_iso()

    output_root = settings.resolved_output_dir
    snapshot_dir = output_root / "snapshots"
    batch_dir = output_root / "batches"
    latest_dir = output_root / "latest"
    state_path = output_root / "state" / "seen_media_candidates.json"

    snapshot_path = (
        snapshot_dir / f"media_candidates_{period}_{args.media_type}_{run_id}.snapshot.json"
    )
    batch_path = args.output or (
        batch_dir / f"media_candidates_{period}_{args.media_type}_{run_id}.batch.json"
    )

    if settings.tmdb_api_key is None:
        raise RuntimeError("环境变量或 .env 中缺少 TMDB_API_KEY。")

    api_key = settings.tmdb_api_key.get_secret_value().strip()
    client = TmdbDiscoveryClient(
        api_key=api_key,
        language=settings.tmdb_language,
        region=settings.tmdb_region,
    )

    try:
        candidates = client.discover(
            year=args.year,
            month=args.month,
            media_types=media_types,
            max_pages=args.max_pages or settings.tmdb_max_pages,
            origin_country=args.origin_country,
            original_language=args.original_language,
        )
    finally:
        client.close()

    state = load_seen_state(state_path)
    new_candidates, updated_state = split_new_candidates(
        candidates,
        state,
        now=discovered_at,
    )

    common_metadata = {
        "run_id": run_id,
        "discovered_at": discovered_at,
        "source": "tmdb",
        "year": args.year,
        "month": args.month,
        "media_type": args.media_type,
        "max_pages": args.max_pages or settings.tmdb_max_pages,
        "total_candidates": len(candidates),
        "new_candidates": len(new_candidates),
        "state_path": str(state_path),
    }

    write_candidates_json(
        candidates,
        snapshot_path,
        metadata={
            **common_metadata,
            "kind": "snapshot",
        },
    )

    write_candidates_json(
        new_candidates,
        batch_path,
        metadata={
            **common_metadata,
            "kind": "batch",
        },
    )

    latest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(snapshot_path, latest_dir / "latest_snapshot.json")
    shutil.copyfile(batch_path, latest_dir / "latest_batch.json")

    if not args.no_update_state:
        save_seen_state(state_path, updated_state)

    print(f"已生成快照：{snapshot_path}")
    print(f"已生成批次：{batch_path}")
    print(f"候选总数：{len(candidates)}")
    print(f"新增候选数：{len(new_candidates)}")
    if args.no_update_state:
        print("已使用 --no-update-state，状态文件未更新。")
    else:
        print(f"已更新状态：{state_path}")


if __name__ == "__main__":
    main()
