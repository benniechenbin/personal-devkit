from __future__ import annotations

import contextvars
import sys
import uuid
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger as logger

from app.config.enums import AppEnv
from app.config.settings import Settings, get_settings

__all__ = [
    "logger",
    "setup_logger",
    "shutdown_logger",
    "add_custom_file",
    "set_trace_id",
    "get_trace_id",
    "trace_id_var",
]

if TYPE_CHECKING:
    from loguru import Record
trace_id_var = contextvars.ContextVar("trace_id", default="system")


def _should_use_json_logs(settings: Settings) -> bool:
    if settings.log_format == "json":
        return True
    if settings.log_format == "pretty":
        return False
    return settings.app_env == AppEnv.PROD


def _patch_record(record: Record) -> None:
    record["extra"].update(trace_id=trace_id_var.get())


def setup_logger(
    log_dir: Path | None = None,
    log_level: str | None = None,
    log_prefix: str = "system",
    app_settings: Settings | None = None,
) -> Path:
    settings = app_settings or get_settings()
    target_dir = log_dir or settings.resolved_log_dir
    target_level = log_level or settings.log_level
    target_dir.mkdir(parents=True, exist_ok=True)

    use_json_logs = _should_use_json_logs(settings)
    is_development = settings.app_env == AppEnv.DEV

    logger.remove()
    logger.configure(patcher=_patch_record)

    if use_json_logs:
        logger.add(
            sys.stdout,
            level=target_level,
            serialize=True,
            enqueue=True,
        )
        logger.add(
            target_dir / f"{log_prefix}_{{time:YYYY-MM-DD}}.jsonl",
            rotation="00:00",
            retention="30 days",
            level=target_level,
            serialize=True,
            enqueue=True,
        )
        return target_dir

    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<magenta>trace_id={extra[trace_id]}</magenta> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "trace_id={extra[trace_id]} | {name}:{line} - {message}"
    )

    logger.add(
        sys.stdout,
        level=target_level,
        colorize=is_development,
        format=console_format,
    )
    logger.add(
        target_dir / f"{log_prefix}_{{time:YYYY-MM-DD}}.log",
        rotation="00:00",
        retention="30 days",
        level=target_level,
        enqueue=True,
        format=file_format,
    )

    return target_dir


def set_trace_id(new_id: str | None = None) -> str:
    trace_id = new_id or uuid.uuid4().hex
    trace_id_var.set(trace_id)
    return trace_id


@contextmanager
def trace_context(trace_id: str | None = None) -> Generator[str, None, None]:
    new_trace_id = trace_id or uuid.uuid4().hex
    token = trace_id_var.set(new_trace_id)
    try:
        yield new_trace_id
    finally:
        trace_id_var.reset(token)


def get_trace_id() -> str:
    return trace_id_var.get()


def shutdown_logger() -> None:
    """
    关闭日志系统。

    作用：
    1. 等待 enqueue=True 的日志写入完成
    2. 移除所有 Loguru handlers
    """
    try:
        logger.complete()
    finally:
        logger.remove()


def add_custom_file(
    file_name: str,
    log_dir: Path | None = None,
    level: str = "INFO",
    filter_rule: str | Callable[..., Any] | None = None,
    app_settings: Settings | None = None,
) -> int:
    settings = app_settings or get_settings()
    target_dir = log_dir or settings.resolved_log_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    return logger.add(
        target_dir / file_name,
        level=level,
        rotation="10 MB",
        filter=filter_rule,
    )
