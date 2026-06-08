from __future__ import annotations

import pytest

from crawl_engine.outputs.markdown_file import (
    append_markdown,
    delete_markdown,
    ensure_directory,
    ensure_md_filename,
    get_available_path,
    join_markdown_sections,
    list_markdown_files,
    read_markdown,
    sanitize_filename,
    save_markdown,
)


def test_sanitize_filename_removes_unsafe_characters() -> None:
    assert sanitize_filename("  demo: title?.md  ") == "demo_ title"
    assert sanitize_filename("///", default="fallback") == "fallback"
    assert sanitize_filename("a" * 100, max_length=10) == "a" * 10


def test_ensure_md_filename_returns_safe_markdown_filename() -> None:
    assert ensure_md_filename("demo title") == "demo title.md"
    assert ensure_md_filename("demo:title?.md") == "demo_title.md"


def test_ensure_directory_creates_folder(tmp_path) -> None:
    folder = tmp_path / "nested" / "folder"

    result = ensure_directory(folder)

    assert result == folder
    assert folder.exists()
    assert folder.is_dir()


def test_save_and_read_markdown(tmp_path) -> None:
    path = save_markdown("# Demo", tmp_path, "demo")

    assert path.name == "demo.md"
    assert path.exists()
    assert read_markdown(path) == "# Demo"


def test_save_markdown_raises_when_file_exists_and_overwrite_disabled(tmp_path) -> None:
    save_markdown("# Demo", tmp_path, "demo")

    with pytest.raises(FileExistsError):
        save_markdown("# New", tmp_path, "demo", overwrite=False)


def test_save_markdown_auto_renames_existing_file(tmp_path) -> None:
    first = save_markdown("# First", tmp_path, "demo")
    second = save_markdown("# Second", tmp_path, "demo", auto_rename=True)

    assert first.name == "demo.md"
    assert second.name == "demo_1.md"
    assert read_markdown(second) == "# Second"


def test_get_available_path_returns_next_available_path(tmp_path) -> None:
    path = tmp_path / "demo.md"
    path.write_text("# Demo", encoding="utf-8")
    (tmp_path / "demo_1.md").write_text("# Demo 1", encoding="utf-8")

    available = get_available_path(path)

    assert available == tmp_path / "demo_2.md"


def test_read_markdown_rejects_non_markdown_suffix(tmp_path) -> None:
    path = tmp_path / "demo.txt"
    path.write_text("hello", encoding="utf-8")

    with pytest.raises(ValueError):
        read_markdown(path)


def test_append_markdown_appends_content(tmp_path) -> None:
    path = save_markdown("# Demo", tmp_path, "demo")

    append_markdown("## Section", path)

    assert read_markdown(path) == "# Demo\n\n## Section"


def test_delete_markdown_deletes_existing_file(tmp_path) -> None:
    path = save_markdown("# Demo", tmp_path, "demo")

    deleted = delete_markdown(path)

    assert deleted is True
    assert not path.exists()


def test_delete_markdown_missing_file_returns_false_by_default(tmp_path) -> None:
    deleted = delete_markdown(tmp_path / "missing.md")

    assert deleted is False


def test_delete_markdown_rejects_non_markdown_file(tmp_path) -> None:
    path = tmp_path / "demo.txt"
    path.write_text("hello", encoding="utf-8")

    with pytest.raises(ValueError):
        delete_markdown(path)


def test_list_markdown_files(tmp_path) -> None:
    save_markdown("# A", tmp_path, "a")
    save_markdown("# B", tmp_path, "b")
    (tmp_path / "note.txt").write_text("ignore", encoding="utf-8")

    files = list_markdown_files(tmp_path)

    assert [file.name for file in files] == ["a.md", "b.md"]


def test_list_markdown_files_recursive(tmp_path) -> None:
    save_markdown("# A", tmp_path, "a")
    nested = tmp_path / "nested"
    save_markdown("# B", nested, "b")

    files = list_markdown_files(tmp_path, recursive=True)

    assert [file.name for file in files] == ["a.md", "b.md"]


def test_join_markdown_sections() -> None:
    result = join_markdown_sections(
        [
            "# Title",
            "",
            "  ## Section  ",
            "Content",
        ]
    )

    assert result == "# Title\n\n## Section\n\nContent"