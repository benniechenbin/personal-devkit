from __future__ import annotations

import json
from pathlib import Path

from subtitle_harvester_app.providers.base import SubtitleSearchResult


def write_subtitle_search_results(
    results: list[SubtitleSearchResult],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "count": len(results),
        "items": [item.to_dict() for item in results],
    }

    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return output_path
