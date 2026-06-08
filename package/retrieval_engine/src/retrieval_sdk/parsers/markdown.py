from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """从 Markdown 内容中提取简单 YAML frontmatter 元数据。"""
    metadata: dict[str, Any] = {"tags": []}
    body_text = content

    yaml_match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not yaml_match:
        return metadata, body_text.strip()

    yaml_text = yaml_match.group(1)
    body_text = content[yaml_match.end() :].strip()

    date_match = re.search(
        r'^date:\s*["\']?(\d{4}[-/]\d{2}[-/]\d{2})["\']?',
        yaml_text,
        re.MULTILINE,
    )
    if date_match:
        metadata["date"] = date_match.group(1).replace("/", "-")

    tags_match = re.search(r"^tags:\s*(.*)", yaml_text, re.MULTILINE)
    if tags_match:
        raw_tags = (
            tags_match.group(1)
            .strip()
            .replace("[", "")
            .replace("]", "")
            .replace('"', "")
            .replace("'", "")
        )
        metadata["tags"] = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]

    return metadata, body_text


def should_include_markdown_file(
    path: Path,
    *,
    ignore_dirs: Iterable[str] = (".obsidian", ".trash"),
    ignore_files: Iterable[str] = (),
) -> bool:
    """判断一个 Markdown 文件是否应被加载。"""
    ignored_dirs = set(ignore_dirs)
    ignored_files = set(ignore_files)
    return (
        path.suffix.lower() == ".md"
        and path.name not in ignored_files
        and not ignored_dirs.intersection(path.parts)
    )
