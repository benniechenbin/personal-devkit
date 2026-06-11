from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

PathLike = str | Path

DEFAULT_ENCODING = "utf-8"
DEFAULT_FILENAME = "untitled"
MARKDOWN_SUFFIX = ".md"


def sanitize_filename(
    filename: str,
    *,
    max_length: int = 80,
    default: str = DEFAULT_FILENAME,
    replacement: str = "_",
) -> str:
    """清理文件名主干，使其适合文件系统使用。"""
    stem = Path(filename).stem.strip()

    safe_chars: list[str] = []
    for char in stem:
        if char.isalnum() or char in (" ", "_", "-"):
            safe_chars.append(char)
        elif replacement:
            safe_chars.append(replacement)

    safe_name = "".join(safe_chars)
    safe_name = " ".join(safe_name.split())
    safe_name = safe_name.strip(" ._-")

    if max_length > 0:
        safe_name = safe_name[:max_length].strip(" ._-")

    return safe_name or default


def ensure_md_filename(filename: str, *, max_length: int = 80) -> str:
    """返回带 .md 后缀的安全 Markdown 文件名。"""
    safe_stem = sanitize_filename(filename, max_length=max_length)
    return f"{safe_stem}{MARKDOWN_SUFFIX}"


def ensure_directory(folder_path: PathLike) -> Path:
    """按需创建目录，并以 Path 形式返回。"""
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_available_path(file_path: PathLike) -> Path:
    """必要时追加 _1、_2 等后缀，返回尚不存在的路径。"""
    path = Path(file_path)

    if not path.exists():
        return path

    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def save_markdown(
    content: str,
    folder_path: PathLike,
    filename: str,
    *,
    overwrite: bool = True,
    auto_rename: bool = False,
    encoding: str = DEFAULT_ENCODING,
) -> Path:
    """
    将内容保存为 Markdown 文件。

    参数：
        content: Markdown 内容。
        folder_path: 目标目录。
        filename: 文件名或标题。
        overwrite: 是否覆盖已有文件。
        auto_rename: 文件已存在时是否生成 name_1.md 形式的新文件名。
        encoding: 文件编码。

    返回：
        已保存文件的路径。
    """
    folder = ensure_directory(folder_path)
    file_path = folder / ensure_md_filename(filename)

    if file_path.exists():
        if auto_rename:
            file_path = get_available_path(file_path)
        elif not overwrite:
            raise FileExistsError(f"Markdown 文件已存在：{file_path}")

    file_path.write_text(content, encoding=encoding)
    return file_path


def read_markdown(
    file_path: PathLike,
    *,
    encoding: str = DEFAULT_ENCODING,
    check_suffix: bool = True,
) -> str:
    """从文件读取 Markdown 内容。"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"未找到 Markdown 文件：{path}")

    if not path.is_file():
        raise IsADirectoryError(f"期望文件，但得到目录：{path}")

    if check_suffix and path.suffix.lower() != MARKDOWN_SUFFIX:
        raise ValueError(f"期望 .md 文件，但得到：{path}")

    return path.read_text(encoding=encoding)


def append_markdown(
    content: str,
    file_path: PathLike,
    *,
    separator: str = "\n\n",
    encoding: str = DEFAULT_ENCODING,
) -> Path:
    """向已有文件追加 Markdown 内容。"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"未找到 Markdown 文件：{path}")

    old_content = path.read_text(encoding=encoding)
    new_content = f"{old_content.rstrip()}{separator}{content.lstrip()}"
    path.write_text(new_content, encoding=encoding)

    return path


def delete_markdown(file_path: PathLike, *, missing_ok: bool = True) -> bool:
    """删除 Markdown 文件；实际删除时返回 True。"""
    path = Path(file_path)

    if not path.exists():
        if missing_ok:
            return False
        raise FileNotFoundError(f"未找到 Markdown 文件：{path}")

    if path.suffix.lower() != MARKDOWN_SUFFIX:
        raise ValueError(f"拒绝删除非 Markdown 文件：{path}")

    path.unlink()
    return True


def list_markdown_files(
    folder_path: PathLike,
    *,
    recursive: bool = False,
) -> list[Path]:
    """列出目录中的 Markdown 文件。"""
    folder = Path(folder_path)

    if not folder.exists():
        return []

    if not folder.is_dir():
        raise NotADirectoryError(f"期望目录，但得到：{folder}")

    pattern = "**/*.md" if recursive else "*.md"
    return sorted(path for path in folder.glob(pattern) if path.is_file())


def join_markdown_sections(sections: Iterable[str]) -> str:
    """用空行拼接多个 Markdown 段落。"""
    return "\n\n".join(section.strip() for section in sections if section and section.strip())
