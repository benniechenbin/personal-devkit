from __future__ import annotations

import zipfile
from pathlib import Path

from core_utils.files import ArchiveExtractor, ArchiveRequest


def _create_zip(path: Path, files: dict[str, str]) -> Path:
    with zipfile.ZipFile(path, "w") as zip_ref:
        for name, content in files.items():
            zip_ref.writestr(name, content)
    return path


def test_archive_extractor_extracts_zip_files(tmp_path: Path) -> None:
    archive_path = _create_zip(
        tmp_path / "demo.zip",
        {
            "a.srt": "subtitle a",
            "nested/b.ass": "subtitle b",
        },
    )
    output_dir = tmp_path / "out"

    extractor = ArchiveExtractor()
    result = extractor.extract(
        ArchiveRequest(
            archive_path=archive_path,
            output_dir=output_dir,
        )
    )

    assert result.success is True
    assert result.output_dir == output_dir
    assert len(result.files) == 2
    assert (output_dir / "a.srt").read_text(encoding="utf-8") == "subtitle a"
    assert (output_dir / "nested" / "b.ass").read_text(encoding="utf-8") == "subtitle b"


def test_archive_extractor_auto_renames_existing_file(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    (output_dir / "a.srt").write_text("old", encoding="utf-8")

    archive_path = _create_zip(
        tmp_path / "demo.zip",
        {
            "a.srt": "new",
        },
    )

    extractor = ArchiveExtractor()
    result = extractor.extract(
        ArchiveRequest(
            archive_path=archive_path,
            output_dir=output_dir,
            auto_rename=True,
        )
    )

    assert result.success is True
    assert (output_dir / "a.srt").read_text(encoding="utf-8") == "old"
    assert (output_dir / "a_1.srt").read_text(encoding="utf-8") == "new"


def test_archive_extractor_rejects_path_traversal(tmp_path: Path) -> None:
    archive_path = _create_zip(
        tmp_path / "evil.zip",
        {
            "../evil.txt": "bad",
        },
    )

    output_dir = tmp_path / "out"

    extractor = ArchiveExtractor()
    result = extractor.extract(
        ArchiveRequest(
            archive_path=archive_path,
            output_dir=output_dir,
        )
    )

    assert result.success is False
    assert result.error_message is not None
    assert "path traversal" in result.error_message
    assert not (tmp_path / "evil.txt").exists()


def test_archive_extractor_returns_failure_for_non_zip(tmp_path: Path) -> None:
    archive_path = tmp_path / "demo.txt"
    archive_path.write_text("not zip", encoding="utf-8")

    extractor = ArchiveExtractor()
    result = extractor.extract(ArchiveRequest(archive_path=archive_path))

    assert result.success is False
    assert result.error_message is not None
    assert "Unsupported archive format" in result.error_message


def test_archive_extractor_can_delete_archive_after_success(tmp_path: Path) -> None:
    archive_path = _create_zip(
        tmp_path / "demo.zip",
        {
            "a.srt": "subtitle",
        },
    )

    extractor = ArchiveExtractor()
    result = extractor.extract(
        ArchiveRequest(
            archive_path=archive_path,
            delete_archive=True,
        )
    )

    assert result.success is True
    assert not archive_path.exists()
