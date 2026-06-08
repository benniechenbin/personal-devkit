from __future__ import annotations

from pathlib import Path


def load_prompt(path: str | Path, *, encoding: str = "utf-8") -> str:
    """加载宿主项目显式传入的 prompt 文件。"""
    return Path(path).read_text(encoding=encoding)
