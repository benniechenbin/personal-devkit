import importlib.util
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "generate_env_example.py"


def _load_env_example_script():
    spec = importlib.util.spec_from_file_location("generate_env_example", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


env_example_script = _load_env_example_script()
build_env_example = env_example_script.build_env_example
write_env_example = env_example_script.write_env_example


def test_build_env_example_from_settings_fields() -> None:
    content = build_env_example(Path("src/subtitle_harvester_app/config/settings.py"))

    assert "# 应用名称，用于启动横幅和日志标识。" in content
    assert "APP_NAME=subtitle-harvester-app" in content
    assert "APP_ENV=development" in content
    assert "LOG_DIR=logs" in content
    assert "LOG_LEVEL=INFO" in content


def test_secret_like_fields_are_blank(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.py"
    settings_file.write_text(
        """
class Settings:
    app_name: str = "demo"
    service_api_key: str = "should-not-leak"
    webhook_token: str = "should-not-leak"
""".strip(),
        encoding="utf-8",
    )

    content = build_env_example(settings_file)

    assert "APP_NAME=demo" in content
    assert "SERVICE_API_KEY=" in content
    assert "WEBHOOK_TOKEN=" in content
    assert "should-not-leak" not in content


def test_write_env_example_reports_when_content_changes(tmp_path: Path) -> None:
    output_file = tmp_path / ".env.example"

    settings_file = Path("src/subtitle_harvester_app/config/settings.py")
    changed = write_env_example(settings_file, output_file)
    unchanged = write_env_example(settings_file, output_file)

    assert changed is True
    assert unchanged is False
