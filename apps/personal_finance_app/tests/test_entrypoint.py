import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_app_module_entrypoint_starts(tmp_path: Path) -> None:
    log_dir = tmp_path / "logs"
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            [
                str(Path(__file__).parent.parent / "src"),
                str(
                    Path(__file__).parent.parent.parent.parent
                    / "packages"
                    / "analysis_engine"
                    / "src"
                ),
                str(
                    Path(__file__).parent.parent.parent.parent
                    / "packages"
                    / "document_engine"
                    / "src"
                ),
                str(
                    Path(__file__).parent.parent.parent.parent / "packages" / "crawl_engine" / "src"
                ),
                str(
                    Path(__file__).parent.parent.parent.parent
                    / "packages"
                    / "retrieval_engine"
                    / "src"
                ),
            ]
        ),
        "APP_NAME": "entrypoint-test",
        "APP_ENV": "test",
        "LOG_LEVEL": "INFO",
        "LOG_DIR": str(log_dir),
    }

    result = subprocess.run(
        [sys.executable, "-m", "personal_finance_app.main", "--help"],
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
    if not entrypoint:
        entrypoint = shutil.which("personal-finance-app")

    assert entrypoint is not None

    log_dir = tmp_path / "logs"
    env = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            [
                str(Path(__file__).parent.parent / "src"),
                str(
                    Path(__file__).parent.parent.parent.parent
                    / "packages"
                    / "analysis_engine"
                    / "src"
                ),
                str(
                    Path(__file__).parent.parent.parent.parent
                    / "packages"
                    / "document_engine"
                    / "src"
                ),
                str(
                    Path(__file__).parent.parent.parent.parent / "packages" / "crawl_engine" / "src"
                ),
                str(
                    Path(__file__).parent.parent.parent.parent
                    / "packages"
                    / "retrieval_engine"
                    / "src"
                ),
            ]
        ),
        "APP_NAME": "console-script-test",
        "APP_ENV": "test",
        "LOG_LEVEL": "INFO",
        "LOG_DIR": str(log_dir),
    }

    result = subprocess.run(
        [entrypoint, "--help"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert log_dir.exists()
    assert any(log_dir.iterdir())
