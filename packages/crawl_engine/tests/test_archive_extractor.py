from __future__ import annotations

import asyncio
import zipfile
from pathlib import Path

from crawl_engine.downloads import ArchiveExtractor
from crawl_engine.schema import ArchiveRequest


def _create_zip(archive_path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(archive_path, "w") as zip_ref:
        for file_name, content in files.items():
            zip_ref.writestr(file_name, content)


def test_archive_extractor_extracts_nested_zip(tmp_path) -> None:
    archive_path = tmp_path / "demo.zip"
    output_dir = tmp_path / "output"
    _create_zip(
        archive_path,
        {
            "root.txt": b"root",
            "nested/report.md": b"nested",
        },
    )

    result = ArchiveExtractor().extract(
        ArchiveRequest(
            archive_path=archive_path,
            output_dir=output_dir,
            metadata={"source": "test"},
        )
    )

    assert result.success is True
    assert result.output_dir == output_dir
    assert result.metadata == {"source": "test"}
    assert sorted(file.file_name for file in result.files) == ["report.md", "root.txt"]
    assert (output_dir / "root.txt").read_bytes() == b"root"
    assert (output_dir / "nested" / "report.md").read_bytes() == b"nested"


def test_archive_extractor_auto_renames_existing_file(tmp_path) -> None:
    archive_path = tmp_path / "demo.zip"
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "demo.txt").write_bytes(b"old")
    _create_zip(archive_path, {"demo.txt": b"new"})

    result = ArchiveExtractor().extract(
        ArchiveRequest(archive_path=archive_path, output_dir=output_dir)
    )

    assert result.success is True
    assert (output_dir / "demo.txt").read_bytes() == b"old"
    assert (output_dir / "demo_1.txt").read_bytes() == b"new"
    assert [file.file_name for file in result.files] == ["demo_1.txt"]


def test_archive_extractor_rejects_path_traversal_before_writing(tmp_path) -> None:
    archive_path = tmp_path / "demo.zip"
    output_dir = tmp_path / "output"
    _create_zip(
        archive_path,
        {
            "safe.txt": b"safe",
            "../evil.txt": b"evil",
        },
    )

    result = ArchiveExtractor().extract(
        ArchiveRequest(archive_path=archive_path, output_dir=output_dir)
    )

    assert result.success is False
    assert result.error_message is not None
    assert "路径穿越" in result.error_message
    assert not (output_dir / "safe.txt").exists()
    assert not (tmp_path / "evil.txt").exists()


def test_archive_extractor_returns_failure_for_non_zip(tmp_path) -> None:
    archive_path = tmp_path / "demo.txt"
    archive_path.write_text("not zip", encoding="utf-8")

    result = ArchiveExtractor().extract(ArchiveRequest(archive_path=archive_path))

    assert result.success is False
    assert result.error_message is not None
    assert "暂不支持" in result.error_message


def test_archive_extractor_deletes_archive_after_success(tmp_path) -> None:
    archive_path = tmp_path / "demo.zip"
    _create_zip(archive_path, {"demo.txt": b"demo"})

    result = ArchiveExtractor().extract(
        ArchiveRequest(archive_path=archive_path, delete_archive=True)
    )

    assert result.success is True
    assert not archive_path.exists()


def test_archive_extractor_enforces_max_files(tmp_path) -> None:
    archive_path = tmp_path / "demo.zip"
    _create_zip(archive_path, {"a.txt": b"a", "b.txt": b"b"})

    result = ArchiveExtractor().extract(ArchiveRequest(archive_path=archive_path, max_files=1))

    assert result.success is False
    assert result.error_message is not None
    assert "文件数量过多" in result.error_message


def test_archive_extractor_enforces_max_total_uncompressed_bytes(tmp_path) -> None:
    archive_path = tmp_path / "demo.zip"
    _create_zip(archive_path, {"big.txt": b"12345"})

    result = ArchiveExtractor().extract(
        ArchiveRequest(archive_path=archive_path, max_total_uncompressed_bytes=4)
    )

    assert result.success is False
    assert result.error_message is not None
    assert "体积过大" in result.error_message


def test_archive_extractor_async_wrapper(tmp_path) -> None:
    archive_path = tmp_path / "demo.zip"
    _create_zip(archive_path, {"demo.txt": b"demo"})

    async def run() -> None:
        result = await ArchiveExtractor().extract_async(ArchiveRequest(archive_path=archive_path))

        assert result.success is True
        assert result.files[0].file_name == "demo.txt"

    asyncio.run(run())
