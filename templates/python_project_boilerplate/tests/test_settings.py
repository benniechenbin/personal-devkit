from pathlib import Path

from python_project_boilerplate.config.settings import BASE_DIR, Settings


def test_relative_log_dir_resolves_from_base_dir() -> None:
    settings = Settings(log_dir=Path("custom-logs"))

    assert settings.resolved_log_dir == BASE_DIR / "custom-logs"


def test_absolute_log_dir_is_kept(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    settings = Settings(log_dir=log_dir)

    assert settings.resolved_log_dir == log_dir


def test_environment_variables_override_defaults(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "demo-service")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_DIR", "custom-logs")

    settings = Settings()

    assert settings.app_name == "demo-service"
    assert settings.app_env == "test"
    assert settings.log_level == "DEBUG"
    assert settings.resolved_log_dir == BASE_DIR / "custom-logs"
