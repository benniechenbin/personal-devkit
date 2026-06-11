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


class DownloadSizeLimitExceeded(RuntimeError):
    """附件下载体积超过调用方声明的限制。"""


class AttachmentDownloader:
    """将已知附件 URL 下载到本地目录。"""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        *,
        verify: bool | str = True,
    ) -> None:
        self.client = client or httpx.AsyncClient(
            verify=verify,
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
            async with self.client.stream(
                "GET",
                request.url,
                headers=request.headers,
                timeout=request.timeout_ms / 1000,
            ) as response:
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
                            error_message=f"文件已存在：{target_path}",
                            metadata=request.metadata,
                        )

                content_length = _parse_content_length(response.headers.get("content-length"))
                if (
                    request.max_size_bytes is not None
                    and content_length is not None
                    and content_length > request.max_size_bytes
                ):
                    return DownloadedFile(
                        success=False,
                        url=request.url,
                        path=target_path,
                        file_name=file_name,
                        content_type=response.headers.get("content-type"),
                        error_message=_size_limit_message(
                            content_length,
                            request.max_size_bytes,
                        ),
                        metadata=request.metadata,
                    )

                temp_path = _get_temp_download_path(target_path)
                try:
                    size_bytes = await _write_response_stream(
                        response,
                        temp_path,
                        max_size_bytes=request.max_size_bytes,
                    )
                    temp_path.replace(target_path)
                except DownloadSizeLimitExceeded as exc:
                    temp_path.unlink(missing_ok=True)
                    return DownloadedFile(
                        success=False,
                        url=request.url,
                        path=target_path,
                        file_name=file_name,
                        content_type=response.headers.get("content-type"),
                        error_message=str(exc),
                        metadata=request.metadata,
                    )
                except Exception:
                    temp_path.unlink(missing_ok=True)
                    raise

                return DownloadedFile(
                    success=True,
                    url=request.url,
                    path=target_path,
                    file_name=file_name,
                    content_type=response.headers.get("content-type"),
                    size_bytes=size_bytes,
                    metadata=request.metadata,
                )

        except httpx.HTTPStatusError as exc:
            logger.exception("附件下载遇到 HTTP 错误：%s", request.url)
            return DownloadedFile(
                success=False,
                url=request.url,
                file_name=request.file_name or "",
                content_type=exc.response.headers.get("content-type"),
                error_message=f"HTTP {exc.response.status_code}",
                metadata=request.metadata,
            )
        except httpx.TimeoutException:
            logger.exception("附件下载超时：%s", request.url)
            return DownloadedFile(
                success=False,
                url=request.url,
                file_name=request.file_name or "",
                error_message="下载超时",
                metadata=request.metadata,
            )
        except Exception as exc:
            logger.exception("附件下载异常崩溃：%s", request.url)
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


def _get_temp_download_path(file_path: str | Path) -> Path:
    path = Path(file_path)
    return _get_available_path(path.with_name(f".{path.name}.part"))


async def _write_response_stream(
    response: httpx.Response,
    target_path: Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_size_bytes: int | None = None,
) -> int:
    size_bytes = 0

    with target_path.open("wb") as target:
        async for chunk in response.aiter_bytes(chunk_size=chunk_size):
            if not chunk:
                continue

            next_size = size_bytes + len(chunk)
            if max_size_bytes is not None and next_size > max_size_bytes:
                raise DownloadSizeLimitExceeded(_size_limit_message(next_size, max_size_bytes))

            target.write(chunk)
            size_bytes = next_size

    return size_bytes


def _parse_content_length(content_length: str | None) -> int | None:
    if not content_length:
        return None

    try:
        return int(content_length)
    except ValueError:
        return None


def _size_limit_message(size_bytes: int, max_size_bytes: int) -> str:
    return f"附件大小超过限制：{size_bytes} > {max_size_bytes}"


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
