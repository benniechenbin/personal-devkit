from __future__ import annotations

import asyncio
import logging
import shutil
import zipfile
from pathlib import Path

from crawl_engine.schema import ArchiveRequest, ExtractedArchive, ExtractedFile

logger = logging.getLogger(__name__)


class ArchiveExtractor:
    """通用压缩包解压器。

    当前第一版只支持 zip。
    不包含任何字幕业务规则，例如删除 .nfo、只保留 .srt 等。
    """

    def extract(self, request: ArchiveRequest) -> ExtractedArchive:
        archive_path = request.archive_path

        if not archive_path.exists():
            return ExtractedArchive(
                success=False,
                archive_path=archive_path,
                error_message=f"压缩包不存在：{archive_path}",
                metadata=request.metadata,
            )

        if not archive_path.is_file():
            return ExtractedArchive(
                success=False,
                archive_path=archive_path,
                error_message=f"期望压缩包文件，但得到目录：{archive_path}",
                metadata=request.metadata,
            )

        if not zipfile.is_zipfile(archive_path):
            return ExtractedArchive(
                success=False,
                archive_path=archive_path,
                error_message=f"暂不支持的压缩包格式：{archive_path.suffix}",
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
            logger.exception("压缩包解压失败：%s", archive_path)
            return ExtractedArchive(
                success=False,
                archive_path=archive_path,
                output_dir=output_dir,
                error_message=str(exc),
                metadata=request.metadata,
            )

    async def extract_async(self, request: ArchiveRequest) -> ExtractedArchive:
        """异步包装，避免在 async pipeline 中阻塞事件循环。"""
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
                raise ValueError(f"压缩包文件数量过多：{len(file_infos)} > {request.max_files}")

            total_uncompressed = sum(max(0, info.file_size) for info in file_infos)
            if total_uncompressed > request.max_total_uncompressed_bytes:
                raise ValueError(
                    "压缩包解压后体积过大："
                    f"{total_uncompressed} > {request.max_total_uncompressed_bytes}"
                )

            for info in file_infos:
                target_path = _safe_target_path(output_dir, info.filename)

                if target_path.exists():
                    if request.auto_rename:
                        target_path = _get_available_path(target_path)
                    elif not request.overwrite:
                        raise FileExistsError(f"文件已存在：{target_path}")

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
    """生成安全解压路径，防止 zip path traversal。"""
    normalized_name = member_name.replace("\\", "/").strip()

    if not normalized_name:
        raise ValueError("压缩包内存在空文件名。")

    member_path = Path(normalized_name)

    if member_path.is_absolute():
        raise ValueError(f"拒绝解压绝对路径文件：{member_name}")

    safe_parts: list[str] = []
    for part in member_path.parts:
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError(f"拒绝解压路径穿越文件：{member_name}")
        safe_parts.append(part)

    if not safe_parts:
        raise ValueError(f"压缩包内文件路径无效：{member_name}")

    target_path = output_dir.joinpath(*safe_parts)

    root = output_dir.resolve()
    target = target_path.resolve()

    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"拒绝解压到目标目录外：{member_name}") from exc

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
