import json
from pathlib import Path

from app.config.enums import AppEnv
from app.config.settings import Settings
from app.observability.logger import (
    get_trace_id,
    set_trace_id,
    setup_logger,
)
from loguru import logger


def test_setup_logger_creates_log_dir(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"

    resolved_dir = setup_logger(log_dir=log_dir, log_level="INFO")

    assert resolved_dir == log_dir
    assert log_dir.exists()


def test_logger_accepts_trace_id(tmp_path: Path) -> None:
    setup_logger(log_dir=tmp_path, log_level="INFO")
    set_trace_id("test-trace")

    logger.info("test message")
    assert get_trace_id() == "test-trace"


def test_setup_logger_uses_injected_settings(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env=AppEnv.TEST,
        log_dir=tmp_path / "injected-logs",
        log_level="DEBUG",
    )

    resolved_dir = setup_logger(app_settings=settings)

    assert resolved_dir == settings.resolved_log_dir


def test_logger_uses_pretty_logs_in_development(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env=AppEnv.DEV,
        log_format="auto",
        log_dir=tmp_path,
    )

    resolved_dir = setup_logger(app_settings=settings)

    assert resolved_dir == tmp_path


def test_logger_uses_json_logs_in_production(tmp_path: Path) -> None:
    settings = Settings(
        _env_file=None,
        app_env=AppEnv.PROD,
        log_format="auto",
        log_dir=tmp_path,
    )

    resolved_dir = setup_logger(app_settings=settings)

    assert resolved_dir == tmp_path

    logger.info("json log test")
    logger.complete()

    log_files = list(tmp_path.glob("*.jsonl"))
    assert log_files

    first_line = log_files[0].read_text(encoding="utf-8").splitlines()[0]
    payload = json.loads(first_line)

    assert isinstance(payload, dict)
