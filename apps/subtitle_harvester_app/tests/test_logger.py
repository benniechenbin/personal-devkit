from pathlib import Path

from loguru import logger

from subtitle_harvester_app.observability.logger import setup_logger


def test_setup_logger_creates_log_dir(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"

    resolved_dir = setup_logger(log_dir=log_dir, log_level="INFO")
    logger.info("test message")
    logger.complete()

    assert resolved_dir == log_dir
    assert log_dir.exists()
    assert any(log_dir.iterdir())
