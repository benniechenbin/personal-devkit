from pathlib import Path

import pytest
from app.config.enums import ModelProvider
from app.config.settings import BASE_DIR, Settings


def test_relative_log_dir_resolves_from_working_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    settings = Settings(_env_file=None, log_dir=Path("test_logs"))

    assert settings.resolved_log_dir == BASE_DIR / "test_logs"


def test_absolute_log_dir_is_preserved(tmp_path: Path) -> None:
    settings = Settings(_env_file=None, log_dir=tmp_path)

    assert settings.resolved_log_dir == tmp_path


def test_openai_api_key_is_secret() -> None:
    settings = Settings(_env_file=None, openai_api_key="sk-test")

    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "sk-test"
    assert "sk-test" not in repr(settings.openai_api_key)


def test_provider_validation_requires_selected_provider_key() -> None:
    settings = Settings(
        _env_file=None,
        default_model_provider=ModelProvider.OPENAI,
        openai_api_key=None,
    )

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        settings.require_provider_credentials()


def test_provider_validation_accepts_selected_provider_key() -> None:
    settings = Settings(
        _env_file=None,
        default_model_provider=ModelProvider.OPENAI,
        openai_api_key="sk-test",
    )

    settings.require_provider_credentials()
