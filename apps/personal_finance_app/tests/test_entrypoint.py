import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_app_module_entrypoint_starts(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    env = {
        **os.environ,
        "APP_NAME": "entrypoint-test",
        "APP_ENV": "test",
        "LOG_LEVEL": "INFO",
        "LOG_DIR": str(log_dir),
    }

    result = subprocess.run(
        [sys.executable, "-m", "personal_finance_app.main"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert log_dir.exists()
    assert any(log_dir.iterdir())


def test_console_script_entrypoint_starts(tmp_path: Path) -> None:
    entrypoint = shutil.which("base-app")
    assert entrypoint is not None

    log_dir = tmp_path / "logs"
    env = {
        **os.environ,
        "APP_NAME": "console-script-test",
        "APP_ENV": "test",
        "LOG_LEVEL": "INFO",
        "LOG_DIR": str(log_dir),
    }

    result = subprocess.run(
        [entrypoint],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert log_dir.exists()
    assert any(log_dir.iterdir())
