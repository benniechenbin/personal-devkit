from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

from crawl_engine.schema import AttachmentRequest, DownloadedFile

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 1024 * 1024
DEFAULT_FILENAME = "attachment"


class AttachmentDownloader:
    """Download known attachment URLs to a local directory."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(
            verify=False,
            timeout=30.0,
            follow_redirects=True,
        )

    async def download(
        self,
        request: AttachmentRequest,
        output_dir: str | Path,
        *,
        overwrite: bool = False,
        auto_rename: bool = True,
    ) -> DownloadedFile:
        target_dir = _ensure_directory(output_dir)

        try:
            response = await self.client.get(
                request.url,
                headers=request.headers,
                timeout=request.timeout_ms / 1000,
            )
            response.raise_for_status()

            file_name = _resolve_file_name(
                explicit_file_name=request.file_name,
                url=request.url,
                content_disposition=response.headers.get("content-disposition"),
            )
            target_path = target_dir / file_name

            if target_path.exists():
                if auto_rename:
                    target_path = _get_available_path(target_path)
                    file_name = target_path.name
                elif not overwrite:
                    return DownloadedFile(
                        success=False,
                        url=request.url,
                        path=target_path,
                        file_name=file_name,
                        content_type=response.headers.get("content-type"),
                        error_message=f"File already exists: {target_path}",
                        metadata=request.metadata,
                    )

            content = response.content
            target_path.write_bytes(content)

            return DownloadedFile(
                success=True,
                url=request.url,
                path=target_path,
                file_name=file_name,
                content_type=response.headers.get("content-type"),
                size_bytes=len(content),
                metadata=request.metadata,
            )

        except httpx.HTTPStatusError as exc:
            logger.exception("Attachment download failed with HTTP error: %s", request.url)
            return DownloadedFile(
                success=False,
                url=request.url,
                file_name=request.file_name or "",
                content_type=exc.response.headers.get("content-type"),
                error_message=f"HTTP {exc.response.status_code}",
                metadata=request.metadata,
            )
        except httpx.TimeoutException:
            logger.exception("Attachment download timed out: %s", request.url)
            return DownloadedFile(
                success=False,
                url=request.url,
                file_name=request.file_name or "",
                error_message="Timeout",
                metadata=request.metadata,
            )
        except Exception as exc:
            logger.exception("Attachment download crashed: %s", request.url)
            return DownloadedFile(
                success=False,
                url=request.url,
                file_name=request.file_name or "",
                error_message=str(exc),
                metadata=request.metadata,
            )

    async def download_many(
        self,
        requests: Sequence[AttachmentRequest],
        output_dir: str | Path,
        *,
        overwrite: bool = False,
        auto_rename: bool = True,
    ) -> list[DownloadedFile]:
        results: list[DownloadedFile] = []
        for request in requests:
            result = await self.download(
                request,
                output_dir,
                overwrite=overwrite,
                auto_rename=auto_rename,
            )
            results.append(result)
        return results

    async def close(self) -> None:
        await self.client.aclose()


def _ensure_directory(folder_path: str | Path) -> Path:
    folder = Path(folder_path)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


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


def _resolve_file_name(
    *,
    explicit_file_name: str | None,
    url: str,
    content_disposition: str | None,
) -> str:
    if explicit_file_name:
        return _safe_file_name(explicit_file_name)

    disposition_name = _extract_filename_from_content_disposition(content_disposition)
    if disposition_name:
        return _safe_file_name(disposition_name)

    parsed = urlparse(url)
    url_name = unquote(Path(parsed.path).name)

    if url_name:
        return _safe_file_name(url_name)

    return f"{DEFAULT_FILENAME}.bin"


def _extract_filename_from_content_disposition(
    content_disposition: str | None,
) -> str | None:
    if not content_disposition:
        return None

    utf8_match = re.search(
        r"filename\*=UTF-8''([^;]+)",
        content_disposition,
        flags=re.IGNORECASE,
    )
    if utf8_match:
        return unquote(utf8_match.group(1).strip().strip('"'))

    normal_match = re.search(
        r'filename="?([^";]+)"?',
        content_disposition,
        flags=re.IGNORECASE,
    )
    if normal_match:
        return unquote(normal_match.group(1).strip())

    return None


def _safe_file_name(file_name: str) -> str:
    decoded_name = unquote(file_name).strip()
    path_name = Path(decoded_name or f"{DEFAULT_FILENAME}.bin")

    suffix = path_name.suffix or ".bin"
    stem = path_name.stem or DEFAULT_FILENAME

    safe_chars: list[str] = []
    for char in stem:
        if char.isalnum() or char in (" ", "_", "-"):
            safe_chars.append(char)
        else:
            safe_chars.append("_")

    safe_stem = "".join(safe_chars)
    safe_stem = " ".join(safe_stem.split())
    safe_stem = safe_stem.strip(" ._-") or DEFAULT_FILENAME

    return f"{safe_stem[:80]}{suffix}"
