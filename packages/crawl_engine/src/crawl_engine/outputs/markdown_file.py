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
    """Clean a filename stem for safe filesystem usage."""
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
    """Return a safe markdown filename with .md suffix."""
    safe_stem = sanitize_filename(filename, max_length=max_length)
    return f"{safe_stem}{MARKDOWN_SUFFIX}"


def ensure_directory(folder_path: PathLike) -> Path:
    """Create a directory if needed and return it as a Path."""
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_available_path(file_path: PathLike) -> Path:
    """Return a non-existing path by appending _1, _2, etc. when needed."""
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
    Save content as a markdown file.

    Args:
        content: Markdown content.
        folder_path: Target folder.
        filename: File name or title.
        overwrite: Whether to overwrite an existing file.
        auto_rename: Whether to generate name_1.md when the file exists.
        encoding: File encoding.

    Returns:
        The saved file path.
    """
    folder = ensure_directory(folder_path)
    file_path = folder / ensure_md_filename(filename)

    if file_path.exists():
        if auto_rename:
            file_path = get_available_path(file_path)
        elif not overwrite:
            raise FileExistsError(f"Markdown file already exists: {file_path}")

    file_path.write_text(content, encoding=encoding)
    return file_path


def read_markdown(
    file_path: PathLike,
    *,
    encoding: str = DEFAULT_ENCODING,
    check_suffix: bool = True,
) -> str:
    """Read markdown content from a file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    if not path.is_file():
        raise IsADirectoryError(f"Expected a file, got directory: {path}")

    if check_suffix and path.suffix.lower() != MARKDOWN_SUFFIX:
        raise ValueError(f"Expected a .md file, got: {path}")

    return path.read_text(encoding=encoding)


def append_markdown(
    content: str,
    file_path: PathLike,
    *,
    separator: str = "\n\n",
    encoding: str = DEFAULT_ENCODING,
) -> Path:
    """Append markdown content to an existing file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    old_content = path.read_text(encoding=encoding)
    new_content = f"{old_content.rstrip()}{separator}{content.lstrip()}"
    path.write_text(new_content, encoding=encoding)

    return path


def delete_markdown(file_path: PathLike, *, missing_ok: bool = True) -> bool:
    """Delete a markdown file. Return True if the file was deleted."""
    path = Path(file_path)

    if not path.exists():
        if missing_ok:
            return False
        raise FileNotFoundError(f"Markdown file not found: {path}")

    if path.suffix.lower() != MARKDOWN_SUFFIX:
        raise ValueError(f"Refuse to delete non-markdown file: {path}")

    path.unlink()
    return True


def list_markdown_files(
    folder_path: PathLike,
    *,
    recursive: bool = False,
) -> list[Path]:
    """List markdown files in a folder."""
    folder = Path(folder_path)

    if not folder.exists():
        return []

    if not folder.is_dir():
        raise NotADirectoryError(f"Expected a directory, got: {folder}")

    pattern = "**/*.md" if recursive else "*.md"
    return sorted(path for path in folder.glob(pattern) if path.is_file())


def join_markdown_sections(sections: Iterable[str]) -> str:
    """Join markdown sections with blank lines."""
    return "\n\n".join(section.strip() for section in sections if section and section.strip())
