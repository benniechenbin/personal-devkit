from pathlib import Path

from scripts.generate_env_example import build_env_example, main, write_env_example


def test_build_env_example_uses_settings_defaults_and_hides_secrets() -> None:
    content = build_env_example()

    assert "APP_ENV=development" in content
    assert "LOG_DIR=logs" in content
    assert "DEFAULT_MODEL_PROVIDER=openai" in content
    assert "OPENAI_API_KEY=\n" in content
    assert "GOOGLE_API_KEY=\n" in content
    assert "GEMINI_API_KEY" not in content


def test_build_env_example_does_not_read_real_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-real-secret")

    content = build_env_example()

    assert "sk-real-secret" not in content
    assert "OPENAI_API_KEY=\n" in content


def test_write_and_check_env_example(tmp_path: Path) -> None:
    output_file = tmp_path / ".env.example"

    assert write_env_example(output_file)
    assert not write_env_example(output_file)
    assert main(["--output", str(output_file), "--check"]) == 0

    output_file.write_text("outdated\n", encoding="utf-8")

    assert main(["--output", str(output_file), "--check"]) == 1
