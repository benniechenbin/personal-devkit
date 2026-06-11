from __future__ import annotations

import json
from pathlib import Path

from subtitle_harvester_app.schema import MediaCandidate


def write_candidates_json(
    candidates: list[MediaCandidate],
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "count": len(candidates),
        "items": [candidate.to_dict() for candidate in candidates],
    }

    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
