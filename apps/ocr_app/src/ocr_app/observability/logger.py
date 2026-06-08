import sys
from collections.abc import Callable
from pathlib import Path

from loguru import logger

from ocr_app.config.settings import settings

__all__ = ["add_custom_file", "logger", "setup_logger"]


def setup_logger(
    log_dir: Path | None = None,
    log_level: str | None = None,
    log_file_name: str = "system_{time:YYYY-MM-DD}.log",
) -> Path:
    target_dir = log_dir or settings.resolved_log_dir
    target_level = log_level or settings.log_level
    target_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stdout,
        level=target_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )
    logger.add(
        target_dir / log_file_name,
        rotation="00:00",
        retention="30 days",
        level=target_level,
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
    )
    return target_dir


def add_custom_file(
    file_name: str,
    log_dir: Path | None = None,
    level: str = "INFO",
    filter_rule: str | Callable[..., bool] | None = None,
) -> int:
    target_dir = log_dir or settings.resolved_log_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    return logger.add(
        target_dir / file_name,
        level=level,
        rotation="10 MB",
        filter=filter_rule,
    )
