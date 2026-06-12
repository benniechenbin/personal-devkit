from __future__ import annotations

import asyncio
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from core_utils.files import ArchiveExtractor, ArchiveRequest

SUBTITLE_SUFFIXES = {".srt", ".ass", ".ssa"}
ARCHIVE_SUFFIXES = {".zip"}
DEFAULT_MAX_SUBTITLE_ARCHIVE_FILES = 50
DEFAULT_MAX_SUBTITLE_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
DEFAULT_MAX_SUBTITLE_FILE_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class ProcessedSubtitlePackage:
    success: bool
    source_path: Path
    output_dir: Path
    subtitle_files: list[Path]
    ignored_files: list[Path]
    error_message: str | None = None


class SubtitlePackageProcessor:
    """处理下载后的字幕包。

    职责：
    - 直接字幕文件：复制到输出目录；
    - zip 压缩包：调用 core_utils.files.ArchiveExtractor 解压；
    - 筛选 .srt / .ass / .ssa；
    - 忽略 .txt / .nfo / .url / .torrent 等非字幕文件。

    不负责：
    - 网络下载；
    - provider 识别；
    - 字幕内容清洗；
    - AI_SUBTITLE_LIBRARY 入库。
    """

    def __init__(
        self,
        extractor: ArchiveExtractor | None = None,
        *,
        max_archive_files: int = DEFAULT_MAX_SUBTITLE_ARCHIVE_FILES,
        max_total_uncompressed_bytes: int = DEFAULT_MAX_SUBTITLE_UNCOMPRESSED_BYTES,
        max_subtitle_file_bytes: int = DEFAULT_MAX_SUBTITLE_FILE_BYTES,
    ) -> None:
        self.extractor = extractor or ArchiveExtractor()
        self.max_archive_files = max_archive_files
        self.max_total_uncompressed_bytes = max_total_uncompressed_bytes
        self.max_subtitle_file_bytes = max_subtitle_file_bytes

    async def process_async(
        self,
        source_path: str | Path,
        output_dir: str | Path,
        *,
        overwrite: bool = False,
    ) -> ProcessedSubtitlePackage:
        return await asyncio.to_thread(
            self.process,
            source_path,
            output_dir,
            overwrite=overwrite,
        )

    def process(
        self,
        source_path: str | Path,
        output_dir: str | Path,
        *,
        overwrite: bool = False,
    ) -> ProcessedSubtitlePackage:
        source = Path(source_path)
        target_dir = Path(output_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        if not source.exists():
            return ProcessedSubtitlePackage(
                success=False,
                source_path=source,
                output_dir=target_dir,
                subtitle_files=[],
                ignored_files=[],
                error_message=f"文件不存在：{source}",
            )

        if not source.is_file():
            return ProcessedSubtitlePackage(
                success=False,
                source_path=source,
                output_dir=target_dir,
                subtitle_files=[],
                ignored_files=[],
                error_message=f"期望文件，但得到目录：{source}",
            )

        suffix = source.suffix.lower()

        if suffix in SUBTITLE_SUFFIXES:
            if not _is_valid_subtitle_file(
                source,
                max_size_bytes=self.max_subtitle_file_bytes,
            ):
                return ProcessedSubtitlePackage(
                    success=False,
                    source_path=source,
                    output_dir=target_dir,
                    subtitle_files=[],
                    ignored_files=[source],
                    error_message="字幕文件无效或为空。",
                )

            copied = _copy_subtitle_file(
                source,
                target_dir,
                overwrite=overwrite,
            )
            return ProcessedSubtitlePackage(
                success=True,
                source_path=source,
                output_dir=target_dir,
                subtitle_files=[copied],
                ignored_files=[],
            )

        if suffix not in ARCHIVE_SUFFIXES:
            return ProcessedSubtitlePackage(
                success=False,
                source_path=source,
                output_dir=target_dir,
                subtitle_files=[],
                ignored_files=[source],
                error_message=f"暂不支持的字幕包格式：{source.suffix}",
            )

        extract_dir = target_dir / source.stem
        extracted = self.extractor.extract(
            ArchiveRequest(
                archive_path=source,
                output_dir=extract_dir,
                overwrite=overwrite,
                auto_rename=not overwrite,
                max_files=self.max_archive_files,
                max_total_uncompressed_bytes=self.max_total_uncompressed_bytes,
            )
        )

        if not extracted.success:
            return ProcessedSubtitlePackage(
                success=False,
                source_path=source,
                output_dir=extract_dir,
                subtitle_files=[],
                ignored_files=[],
                error_message=extracted.error_message,
            )

        subtitle_files: list[Path] = []
        ignored_files: list[Path] = []

        for extracted_file in extracted.files:
            path = extracted_file.path
            if path.suffix.lower() in SUBTITLE_SUFFIXES and _is_valid_subtitle_file(
                path,
                max_size_bytes=self.max_subtitle_file_bytes,
            ):
                subtitle_files.append(path)
            else:
                ignored_files.append(path)

        return ProcessedSubtitlePackage(
            success=bool(subtitle_files),
            source_path=source,
            output_dir=extract_dir,
            subtitle_files=sorted(subtitle_files),
            ignored_files=sorted(ignored_files),
            error_message=None if subtitle_files else "未找到可用字幕文件。",
        )


def _copy_subtitle_file(
    source: Path,
    output_dir: Path,
    *,
    overwrite: bool,
) -> Path:
    target = output_dir / source.name

    if target.exists() and not overwrite:
        target = _get_available_path(target)

    shutil.copy2(source, target)
    return target


def _get_available_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    index = 1
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _is_valid_subtitle_file(path: Path, *, max_size_bytes: int) -> bool:
    try:
        size = path.stat().st_size
    except OSError:
        return False

    if size <= 0 or size > max_size_bytes:
        return False

    try:
        sample = path.read_bytes()[: 64 * 1024]
    except OSError:
        return False

    text = _decode_subtitle_sample(sample)
    if not text or _looks_like_binary(sample):
        return False

    suffix = path.suffix.lower()
    if suffix == ".srt":
        return bool(re.search(r"\d{1,2}:\d{2}:\d{2}[,.]\d{1,3}\s*-->\s*", text))
    if suffix in {".ass", ".ssa"}:
        return "[script info]" in text.lower() or "dialogue:" in text.lower()

    return False


def _decode_subtitle_sample(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "utf-16"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def _looks_like_binary(content: bytes) -> bool:
    if not content:
        return False
    if content.startswith((b"\xff\xfe", b"\xfe\xff")):
        return False
    return content.count(b"\x00") > 0
