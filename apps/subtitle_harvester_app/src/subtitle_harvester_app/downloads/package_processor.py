from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from core_utils.files import ArchiveExtractor, ArchiveRequest

SUBTITLE_SUFFIXES = {".srt", ".ass", ".ssa"}
ARCHIVE_SUFFIXES = {".zip"}


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

    def __init__(self, extractor: ArchiveExtractor | None = None) -> None:
        self.extractor = extractor or ArchiveExtractor()

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
            if path.suffix.lower() in SUBTITLE_SUFFIXES:
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
