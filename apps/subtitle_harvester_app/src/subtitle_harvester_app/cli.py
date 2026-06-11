from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from subtitle_harvester_app.config.settings import get_settings
from subtitle_harvester_app.core.bootstrap import init_workspace
from subtitle_harvester_app.discovery.tmdb_discovery import TmdbDiscoveryClient
from subtitle_harvester_app.outputs.json_writer import write_candidates_json
from subtitle_harvester_app.schema import MediaType


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从 TMDb 获取影视候选片单，并输出 JSON。",
    )
    parser.add_argument("--year", type=int, default=datetime.now().year)
    parser.add_argument("--month", type=int, default=None)
    parser.add_argument(
        "--media-type",
        choices=["movie", "tv", "all"],
        default="all",
    )
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = init_workspace(get_settings())

    media_types: tuple[MediaType, ...]
    if args.media_type == "all":
        media_types = ("movie", "tv")
    else:
        media_types = (args.media_type,)

    month_part = f"_{args.month:02d}" if args.month else ""
    default_output = (
        settings.resolved_output_dir
        / f"media_candidates_{args.year}{month_part}_{args.media_type}.json"
    )
    output_path = args.output or default_output

    api_key = settings.tmdb_api_key.get_secret_value()
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
        )
    finally:
        client.close()

    write_candidates_json(candidates, output_path)

    print(f"✅ 已生成候选片单：{output_path}")
    print(f"📦 共 {len(candidates)} 条")


if __name__ == "__main__":
    main()
