from pathlib import Path

from ocr_app.config.settings import BASE_DIR, Settings


def test_settings_resolve_relative_paths() -> None:
    settings = Settings(_env_file=None, log_dir=Path("logs-test"), output_dir=Path("out-test"))

    assert settings.resolved_log_dir == BASE_DIR / "logs-test"
    assert settings.resolved_output_dir == BASE_DIR / "out-test"
