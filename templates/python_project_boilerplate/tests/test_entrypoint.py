from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"


def _build_subprocess_env(tmp_path: Path) -> dict[str, str]:
    log_dir = tmp_path / "logs"
    existing_pythonpath = os.environ.get("PYTHONPATH", "")

    env = {
        **os.environ,
        "APP_NAME": "entrypoint-test",
        "APP_ENV": "test",
        "LOG_LEVEL": "INFO",
        "LOG_DIR": str(log_dir),
        "PYTHONPATH": str(SRC_DIR)
        if not existing_pythonpath
        else f"{SRC_DIR}{os.pathsep}{existing_pythonpath}",
    }
    return env


def test_app_module_entrypoint_starts(tmp_path: Path) -> None:
    env = _build_subprocess_env(tmp_path)
    log_dir = Path(env["LOG_DIR"])

    result = subprocess.run(
        [sys.executable, "-m", "python_project_boilerplate.main"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert log_dir.exists()
    assert any(log_dir.iterdir())


def test_app_main_callable_starts(tmp_path: Path) -> None:
    env = _build_subprocess_env(tmp_path)
    log_dir = Path(env["LOG_DIR"])

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from python_project_boilerplate.main import main; main()",
        ],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert log_dir.exists()
    assert any(log_dir.iterdir())
