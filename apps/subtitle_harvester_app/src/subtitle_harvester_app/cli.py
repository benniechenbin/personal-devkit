from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from subtitle_harvester_app.commands.discover import run_discover_command


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
    parser.add_argument(
        "--sort-by",
        default=None,
        help="TMDb discover 排序方式，例如 popularity.desc。",
    )
    parser.add_argument(
        "--min-vote-count",
        type=_non_negative_int,
        default=None,
        help="最低投票数过滤，对应 TMDb vote_count.gte。",
    )
    parser.add_argument(
        "--min-runtime",
        type=_positive_int,
        default=None,
        help="最低片长分钟数过滤，对应 TMDb with_runtime.gte。",
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


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("值必须大于等于 0")
    return parsed


def _run_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    run_discover_command(args, run_id=_run_id())


if __name__ == "__main__":
    main()
