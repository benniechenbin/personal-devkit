from __future__ import annotations

import contextvars
import sys
import uuid
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger as logger

_settings_loader: Callable[[], Any] | None
try:
    from ..config.settings import (  # type: ignore[misc, unused-ignore]
        get_settings as _imported_get_settings,
    )
except (ImportError, ValueError):
    _settings_loader = None
else:
    _settings_loader = _imported_get_settings

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

# 全局追踪 ID 变量
trace_id_var = contextvars.ContextVar("trace_id", default="system")


def _should_use_json_logs(settings: Any) -> bool:
    if not settings:
        return False

    log_format = str(getattr(settings, "log_format", "auto"))
    app_env = _settings_value(getattr(settings, "app_env", "development"))

    if log_format == "json":
        return True
    if log_format == "pretty":
        return False

    return app_env in ("production", "prod")


def _settings_value(value: Any) -> str:
    if hasattr(value, "value"):
        value = value.value
    return str(value)


def _default_settings() -> Any | None:
    if _settings_loader is None:
        return None
    return _settings_loader()


def _resolve_log_dir(log_dir: Path | None, settings: Any | None) -> Path:
    if log_dir is not None:
        return log_dir
    if settings is None:
        return Path("logs")

    resolved = getattr(settings, "resolved_log_dir", None)
    if isinstance(resolved, Path):
        return resolved
    if resolved is not None:
        return Path(resolved)
    return Path("logs")


def _resolve_log_level(log_level: str | None, settings: Any | None) -> str:
    if log_level is not None:
        return log_level
    if settings is None:
        return "INFO"
    return str(getattr(settings, "log_level", "INFO") or "INFO")


def _patch_record(record: Record) -> None:
    record["extra"].update(trace_id=trace_id_var.get())


def setup_logger(
    log_dir: Path | None = None,
    log_level: str | None = None,
    log_prefix: str = "system",
    app_settings: Any | None = None,
) -> Path:
    """
    配置日志系统，支持控制台彩色输出、文件滚动记录以及可选的 JSON 格式。
    """
    settings = app_settings or _default_settings()

    target_dir = _resolve_log_dir(log_dir, settings)
    target_level = _resolve_log_level(log_level, settings)

    target_dir.mkdir(parents=True, exist_ok=True)

    use_json_logs = _should_use_json_logs(settings)

    app_env = _settings_value(getattr(settings, "app_env", "development"))
    is_development = app_env in ("development", "dev")

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
    """手动设置当前的追踪 ID。"""
    trace_id = new_id or uuid.uuid4().hex
    trace_id_var.set(trace_id)
    return trace_id


@contextmanager
def trace_context(trace_id: str | None = None) -> Generator[str, None, None]:
    """追踪上下文管理器，离开时自动恢复。"""
    new_trace_id = trace_id or uuid.uuid4().hex
    token = trace_id_var.set(new_trace_id)
    try:
        yield new_trace_id
    finally:
        trace_id_var.reset(token)


def get_trace_id() -> str:
    """获取当前的追踪 ID。"""
    return trace_id_var.get()


def shutdown_logger() -> None:
    """优雅关闭日志，确保 enqueue 的日志已写盘。"""
    try:
        logger.complete()
    finally:
        logger.remove()


def add_custom_file(
    file_name: str,
    log_dir: Path | None = None,
    level: str = "INFO",
    filter_rule: str | Callable[..., Any] | None = None,
    app_settings: Any | None = None,
) -> int:
    """运行时动态添加日志文件。"""
    settings = app_settings or _default_settings()
    target_dir = _resolve_log_dir(log_dir, settings)
    target_dir.mkdir(parents=True, exist_ok=True)
    return logger.add(
        target_dir / file_name,
        level=level,
        rotation="10 MB",
        filter=filter_rule,
    )
