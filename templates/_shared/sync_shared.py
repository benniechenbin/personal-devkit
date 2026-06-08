from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SHARED_DIR = ROOT_DIR / "templates" / "_shared"


@dataclass(frozen=True)
class SharedFile:
    source: Path
    targets: tuple[Path, ...]


SHARED_FILES = (
    SharedFile(
        source=SHARED_DIR / "core" / "banner.py",
        targets=(
            ROOT_DIR
            / "templates"
            / "python_project_boilerplate"
            / "src"
            / "python_project_boilerplate"
            / "core"
            / "banner.py",
            ROOT_DIR
            / "templates"
            / "python_project_boilerplate"
            / "template"
            / "src"
            / "{{ package_name }}"
            / "core"
            / "banner.py",
            ROOT_DIR
            / "templates"
            / "agent_enterprise_boilerplate"
            / "src"
            / "app"
            / "core"
            / "banner.py",
        ),
    ),
)


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def sync_shared_files(*, check: bool = False) -> int:
    changed: list[Path] = []

    for shared_file in SHARED_FILES:
        source_content = _read_bytes(shared_file.source)
        for target in shared_file.targets:
            if target.exists() and _read_bytes(target) == source_content:
                continue

            changed.append(target)
            if not check:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(shared_file.source, target)

    if changed:
        verb = "would update" if check else "updated"
        for path in changed:
            print(f"{verb}: {path.relative_to(ROOT_DIR)}")
        return 1 if check else 0

    print("shared template files are in sync")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync shared template maintenance files into self-contained templates."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if generated template copies differ from templates/_shared.",
    )
    args = parser.parse_args()
    return sync_shared_files(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
