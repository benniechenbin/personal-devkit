from __future__ import annotations

import asyncio
import logging
import shutil
import zipfile
from pathlib import Path

from core_utils.files.schema import ArchiveRequest, ExtractedArchive, ExtractedFile

logger = logging.getLogger(__name__)


class ArchiveExtractor:
    """Generic archive extractor.

    Currently supports zip archives only. It contains no domain-specific filtering
    rules, so higher-level packages can decide which extracted files they need.
    """

    def extract(self, request: ArchiveRequest) -> ExtractedArchive:
        archive_path = request.archive_path

        if not archive_path.exists():
            return ExtractedArchive(
                success=False,
                archive_path=archive_path,
                error_message=f"Archive does not exist: {archive_path}",
                metadata=request.metadata,
            )

        if not archive_path.is_file():
            return ExtractedArchive(
                success=False,
                archive_path=archive_path,
                error_message=f"Expected archive file, got directory: {archive_path}",
                metadata=request.metadata,
            )

        if not zipfile.is_zipfile(archive_path):
            return ExtractedArchive(
                success=False,
                archive_path=archive_path,
                error_message=f"Unsupported archive format: {archive_path.suffix}",
                metadata=request.metadata,
            )

        output_dir = request.output_dir or archive_path.parent / archive_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            extracted_files = self._extract_zip(archive_path, output_dir, request)

            if request.delete_archive:
                archive_path.unlink(missing_ok=True)

            return ExtractedArchive(
                success=True,
                archive_path=archive_path,
                output_dir=output_dir,
                files=extracted_files,
                metadata=request.metadata,
            )

        except Exception as exc:
            logger.exception("Archive extraction failed: %s", archive_path)
            return ExtractedArchive(
                success=False,
                archive_path=archive_path,
                output_dir=output_dir,
                error_message=str(exc),
                metadata=request.metadata,
            )

    async def extract_async(self, request: ArchiveRequest) -> ExtractedArchive:
        """Run extraction in a worker thread for async pipelines."""
        return await asyncio.to_thread(self.extract, request)

    def _extract_zip(
        self,
        archive_path: Path,
        output_dir: Path,
        request: ArchiveRequest,
    ) -> list[ExtractedFile]:
        extracted_files: list[ExtractedFile] = []

        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            file_infos = [info for info in zip_ref.infolist() if not info.is_dir()]

            if len(file_infos) > request.max_files:
                raise ValueError(
                    f"Archive contains too many files: {len(file_infos)} > {request.max_files}"
                )

            total_uncompressed = sum(max(0, info.file_size) for info in file_infos)
            if total_uncompressed > request.max_total_uncompressed_bytes:
                raise ValueError(
                    "Archive uncompressed size exceeds limit: "
                    f"{total_uncompressed} > {request.max_total_uncompressed_bytes}"
                )

            target_paths = [_safe_target_path(output_dir, info.filename) for info in file_infos]

            for info, target_path in zip(file_infos, target_paths, strict=True):
                if target_path.exists():
                    if request.auto_rename:
                        target_path = _get_available_path(target_path)
                    elif not request.overwrite:
                        raise FileExistsError(f"File already exists: {target_path}")

                target_path.parent.mkdir(parents=True, exist_ok=True)

                with zip_ref.open(info, "r") as source, target_path.open("wb") as target:
                    shutil.copyfileobj(source, target)

                extracted_files.append(
                    ExtractedFile(
                        path=target_path,
                        file_name=target_path.name,
                        suffix=target_path.suffix.lower(),
                        size_bytes=target_path.stat().st_size,
                    )
                )

        return extracted_files


def _safe_target_path(output_dir: Path, member_name: str) -> Path:
    normalized_name = member_name.replace("\\", "/").strip()

    if not normalized_name:
        raise ValueError("Archive member has an empty file name.")

    member_path = Path(normalized_name)

    if member_path.is_absolute():
        raise ValueError(f"Refusing to extract absolute path member: {member_name}")

    safe_parts: list[str] = []
    for part in member_path.parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError(f"Refusing to extract path traversal member: {member_name}")
        safe_parts.append(part)

    if not safe_parts:
        raise ValueError(f"Archive member path is invalid: {member_name}")

    target_path = output_dir.joinpath(*safe_parts)

    root = output_dir.resolve()
    target = target_path.resolve()

    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Refusing to extract outside target directory: {member_name}") from exc

    return target_path


def _get_available_path(file_path: str | Path) -> Path:
    path = Path(file_path)

    if not path.exists():
        return path

    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1
