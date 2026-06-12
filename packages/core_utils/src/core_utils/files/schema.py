from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ArchiveRequest(BaseModel):
    archive_path: Path
    output_dir: Path | None = None
    overwrite: bool = False
    auto_rename: bool = True
    delete_archive: bool = False
    max_files: int = 1000
    max_total_uncompressed_bytes: int = 500 * 1024 * 1024
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedFile(BaseModel):
    path: Path
    file_name: str
    suffix: str
    size_bytes: int


class ExtractedArchive(BaseModel):
    success: bool
    archive_path: Path
    output_dir: Path | None = None
    files: list[ExtractedFile] = Field(default_factory=list)
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
