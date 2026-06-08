from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    timeout_ms: int = 30_000
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScrapeResponse(BaseModel):
    success: bool
    url: str
    content: str = ""
    raw_html: str = ""
    content_length: int = 0
    status_code: int | None = None
    final_url: str | None = None
    content_type: str | None = None
    extracted_data: Any | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Crawl4AIRequest(ScrapeRequest):
    remove_noise: bool = True
    max_length: int = 10_000
    css_schema: dict[str, Any] | None = None
    wait_for: str | None = None
    js_code: list[str] | None = None


class AttachmentRequest(BaseModel):
    url: str
    file_name: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DownloadedFile(BaseModel):
    success: bool
    url: str
    path: Path | None = None
    file_name: str = ""
    content_type: str | None = None
    size_bytes: int | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
