from __future__ import annotations

import ast
import sys
from pathlib import Path

Rule = tuple[str, set[str], str]

# Format: (path_prefix, forbidden_import_roots, reason)
FORBIDDEN_RULES: list[Rule] = [
    (
        "packages/",
        {"apps", "templates"},
        "Packages must not depend on applications or templates.",
    ),
    (
        "packages/analysis_engine/",
        {"crawl_engine", "document_engine", "retrieval_engine"},
        "analysis_engine should be a pure domain core and not depend on other engines.",
    ),
]

STRICT_CORE_RULES: list[Rule] = [
    (
        "packages/analysis_engine/src/",
        {"aiohttp", "httpx", "neo4j", "pymongo", "qdrant_client", "requests", "sqlalchemy"},
        "analysis_engine should be deterministic and IO-free.",
    )
]


def get_imports(file_path: Path) -> set[str]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError) as exc:
        print(f"Warning: could not parse {file_path}: {exc}")
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def check_boundaries() -> bool:
    root = Path(".")
    errors: list[str] = []
    all_rules = FORBIDDEN_RULES + STRICT_CORE_RULES

    for file_path in root.rglob("*.py"):
        relative_path = file_path.relative_to(root).as_posix()
        active_rules = [
            (forbidden, reason)
            for prefix, forbidden, reason in all_rules
            if relative_path.startswith(prefix)
        ]
        if not active_rules:
            continue

        for forbidden_prefixes, reason in active_rules:
            for imported_module in get_imports(file_path):
                for forbidden in forbidden_prefixes:
                    if imported_module == forbidden or imported_module.startswith(f"{forbidden}."):
                        errors.append(
                            f"Violation in {relative_path}:\n"
                            f"  Import: {imported_module!r}\n"
                            f"  Rule: {reason}"
                        )

    if errors:
        print(f"Found {len(errors)} boundary violations:\n")
        print("\n" + "-" * 40 + "\n".join(errors))
        return False

    print("No boundary violations found.")
    return True


if __name__ == "__main__":
    sys.exit(0 if check_boundaries() else 1)
