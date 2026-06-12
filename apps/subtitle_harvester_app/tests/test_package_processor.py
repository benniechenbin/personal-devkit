from __future__ import annotations

import zipfile
from pathlib import Path

from subtitle_harvester_app.downloads.package_processor import (
    SubtitlePackageProcessor,
)


def test_package_processor_extracts_subtitle_files_from_zip(tmp_path: Path) -> None:
    archive_path = tmp_path / "demo.zip"
    output_dir = tmp_path / "processed"

    with zipfile.ZipFile(archive_path, "w") as zip_file:
        zip_file.writestr("movie.zh.srt", "1\n00:00:01,000 --> 00:00:02,000\n你好\n")
        zip_file.writestr("movie.zh.ass", "[Script Info]\n")
        zip_file.writestr("readme.txt", "ignore me")
        zip_file.writestr("nested/notes.nfo", "ignore me too")

    processor = SubtitlePackageProcessor()
    result = processor.process(archive_path, output_dir)

    assert result.success is True
    assert result.source_path == archive_path
    assert result.output_dir == output_dir / "demo"

    assert [path.name for path in result.subtitle_files] == [
        "movie.zh.ass",
        "movie.zh.srt",
    ]
    assert sorted(path.name for path in result.ignored_files) == [
        "notes.nfo",
        "readme.txt",
    ]

    assert (output_dir / "demo" / "movie.zh.srt").exists()
    assert (output_dir / "demo" / "movie.zh.ass").exists()


def test_package_processor_accepts_direct_subtitle_file(tmp_path: Path) -> None:
    source_path = tmp_path / "movie.srt"
    output_dir = tmp_path / "processed"

    source_path.write_text(
        "1\n00:00:01,000 --> 00:00:02,000\n你好\n",
        encoding="utf-8",
    )

    processor = SubtitlePackageProcessor()
    result = processor.process(source_path, output_dir)

    assert result.success is True
    assert result.subtitle_files == [output_dir / "movie.srt"]
    assert result.ignored_files == []
    assert (output_dir / "movie.srt").read_text(encoding="utf-8").endswith("你好\n")


def test_package_processor_returns_failure_when_zip_has_no_subtitles(
    tmp_path: Path,
) -> None:
    archive_path = tmp_path / "demo.zip"
    output_dir = tmp_path / "processed"

    with zipfile.ZipFile(archive_path, "w") as zip_file:
        zip_file.writestr("readme.txt", "ignore me")
        zip_file.writestr("info.nfo", "ignore me too")

    processor = SubtitlePackageProcessor()
    result = processor.process(archive_path, output_dir)

    assert result.success is False
    assert result.subtitle_files == []
    assert sorted(path.name for path in result.ignored_files) == [
        "info.nfo",
        "readme.txt",
    ]
    assert result.error_message == "未找到可用字幕文件。"


def test_package_processor_ignores_invalid_subtitle_files(tmp_path: Path) -> None:
    archive_path = tmp_path / "demo.zip"
    output_dir = tmp_path / "processed"

    with zipfile.ZipFile(archive_path, "w") as zip_file:
        zip_file.writestr("empty.srt", "")
        zip_file.writestr("fake.srt", "not a subtitle")

    processor = SubtitlePackageProcessor()
    result = processor.process(archive_path, output_dir)

    assert result.success is False
    assert result.subtitle_files == []
    assert sorted(path.name for path in result.ignored_files) == ["empty.srt", "fake.srt"]


def test_package_processor_enforces_app_archive_file_limit(tmp_path: Path) -> None:
    archive_path = tmp_path / "demo.zip"
    output_dir = tmp_path / "processed"

    with zipfile.ZipFile(archive_path, "w") as zip_file:
        zip_file.writestr("one.srt", "1\n00:00:01,000 --> 00:00:02,000\nhello\n")
        zip_file.writestr("two.srt", "1\n00:00:01,000 --> 00:00:02,000\nhello\n")

    processor = SubtitlePackageProcessor(max_archive_files=1)
    result = processor.process(archive_path, output_dir)

    assert result.success is False
    assert result.error_message is not None
    assert "too many files" in result.error_message


def test_package_processor_rejects_unsupported_package_format(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "demo.txt"
    output_dir = tmp_path / "processed"

    source_path.write_text("not a subtitle package", encoding="utf-8")

    processor = SubtitlePackageProcessor()
    result = processor.process(source_path, output_dir)

    assert result.success is False
    assert result.subtitle_files == []
    assert result.ignored_files == [source_path]
    assert result.error_message == "暂不支持的字幕包格式：.txt"


def test_package_processor_returns_failure_for_missing_file(tmp_path: Path) -> None:
    source_path = tmp_path / "missing.zip"
    output_dir = tmp_path / "processed"

    processor = SubtitlePackageProcessor()
    result = processor.process(source_path, output_dir)

    assert result.success is False
    assert result.subtitle_files == []
    assert result.ignored_files == []
    assert result.error_message == f"文件不存在：{source_path}"
