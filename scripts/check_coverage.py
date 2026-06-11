from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

TARGETS = {
    "analysis_engine": 80,
    "crawl_engine": 80,
    "document_engine": 30,
    "retrieval_engine": 80,
    "ocr_app": 25,
    "personal_finance_app": 20,
    "subtitle_harvester_app": 50,
}


def get_coverage_data() -> dict[str, Any]:
    subprocess.run(["uv", "run", "coverage", "json"], check=True)
    return cast(dict[str, Any], json.loads(Path("coverage.json").read_text(encoding="utf-8")))


def package_name_from_path(file_path: str) -> str | None:
    parts = Path(file_path).parts
    if "packages" in parts:
        return parts[parts.index("packages") + 1]
    if "apps" in parts:
        return parts[parts.index("apps") + 1]
    return None


def check_coverage() -> bool:
    try:
        data = get_coverage_data()
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"Error getting coverage data: {exc}")
        return False

    package_stats: dict[str, dict[str, int]] = {}
    for file_path, stats in data.get("files", {}).items():
        package_name = package_name_from_path(file_path)
        if package_name is None:
            continue

        current = package_stats.setdefault(package_name, {"covered": 0, "total": 0})
        summary = stats["summary"]
        current["covered"] += int(summary["covered_lines"])
        current["total"] += int(summary["num_statements"])

    errors: list[str] = []
    print("Package Coverage Report:")
    print(f"{'Package':<30} | {'Coverage':<10} | {'Target':<10} | Status")
    print("-" * 70)

    for package_name, target in TARGETS.items():
        stats = package_stats.get(package_name)
        if not stats or stats["total"] == 0:
            errors.append(f"{package_name}: coverage data is missing")
            print(f"{package_name:<30} | {'N/A':<10} | {target:<10}% | MISSING")
            continue

        actual = (stats["covered"] / stats["total"]) * 100
        status = "OK" if actual >= target else "FAIL"
        print(f"{package_name:<30} | {actual:>8.2f}% | {target:>8}% | {status}")

        if actual < target:
            errors.append(f"{package_name}: coverage {actual:.2f}% is below target {target}%")

    if errors:
        print("\nCoverage failures:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


if __name__ == "__main__":
    sys.exit(0 if check_coverage() else 1)
