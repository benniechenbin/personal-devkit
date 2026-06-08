from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
COPIER_COMMAND = ["uv", "tool", "run", "copier"]
COPY_IGNORE = shutil.ignore_patterns(
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "*.pyc",
    ".coverage",
    ".env",
    "dist",
    "build",
    "logs",
)


def _run(command: list[str], cwd: Path) -> None:
    env = {
        **os.environ,
        "UV_LINK_MODE": "copy",
        "APP_ENV": "test",
        "LOG_DIR": str(cwd / "logs"),
    }
    env.pop("VIRTUAL_ENV", None)
    env.pop("UV_PROJECT_ENVIRONMENT", None)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def _prepare_template_repo(temporary_root: Path) -> Path:
    template_repo = temporary_root / "template-repo"
    shutil.copytree(ROOT_DIR, template_repo, ignore=COPY_IGNORE)
    commands = [
        ["git", "init"],
        ["git", "config", "user.name", "Copier Template Check"],
        ["git", "config", "user.email", "copier-template-check@example.com"],
        ["git", "add", "."],
        ["git", "commit", "-m", "Template test fixture"],
        ["git", "tag", "v0.1.0"],
    ]
    for command in commands:
        _run(command, template_repo)
    return template_repo


def _generate_project(template_repo: Path, destination: Path, project_name: str) -> None:
    _run(
        [
            *COPIER_COMMAND,
            "copy",
            "--vcs-ref",
            "HEAD",
            "--defaults",
            "--data",
            f"project_name={project_name}",
            str(template_repo),
            str(destination),
        ],
        template_repo,
    )


def _assert_generated_project(destination: Path, project_name: str, package_name: str) -> None:
    package_dir = destination / "src" / package_name
    assert package_dir.is_dir(), f"Missing generated package directory: {package_dir}"
    assert not (destination / "src" / "app").exists(), "Generated project still contains src/app"
    assert (destination / ".copier-answers.yml").is_file(), "Missing Copier answers file"

    pyproject = (destination / "pyproject.toml").read_text(encoding="utf-8")
    assert f'name = "{project_name}"' in pyproject
    assert f'packages = ["src/{package_name}"]' in pyproject
    assert f'base-app = "{package_name}.main:main"' in pyproject

    env_example = (destination / ".env.example").read_text(encoding="utf-8")
    assert f"APP_NAME={project_name}" in env_example


def _initialize_project_repo(destination: Path) -> None:
    commands = [
        ["git", "init"],
        ["git", "config", "user.name", "Copier Project Check"],
        ["git", "config", "user.email", "copier-project-check@example.com"],
        ["git", "add", "."],
        ["git", "commit", "-m", "Generated project"],
    ]
    for command in commands:
        _run(command, destination)


def _evolve_template_repo(template_repo: Path) -> None:
    readme_template = template_repo / "template" / "README.md.jinja"
    readme_template.write_text(
        readme_template.read_text(encoding="utf-8")
        + "\nTemplate update check for {{ project_name }}.\n",
        encoding="utf-8",
    )
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", "Template update fixture"],
        ["git", "tag", "v0.2.0"],
    ]
    for command in commands:
        _run(command, template_repo)


def _update_project(destination: Path) -> None:
    _run(
        [
            *COPIER_COMMAND,
            "update",
            "--vcs-ref",
            "HEAD",
            "--defaults",
            str(destination),
        ],
        destination,
    )


def _validate_project(destination: Path, package_name: str) -> None:
    commands = [
        ["uv", "lock", "--check"],
        ["uv", "sync", "--locked", "--extra", "dev"],
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "ruff", "format", ".", "--check"],
        ["uv", "run", "mypy", "src"],
        ["uv", "run", "python", "scripts/generate_env_example.py", "--check"],
        ["uv", "run", "pytest"],
        ["uv", "run", "base-app"],
        ["uv", "run", "python", "-m", f"{package_name}.main"],
    ]
    for command in commands:
        _run(command, destination)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="python-base-template-") as temporary_dir:
        temporary_root = Path(temporary_dir)
        template_repo = _prepare_template_repo(temporary_root)
        destination = temporary_root / "order-service"

        _generate_project(template_repo, destination, "order-service")
        _assert_generated_project(destination, "order-service", "order_service")
        _validate_project(destination, "order_service")

        _initialize_project_repo(destination)
        _evolve_template_repo(template_repo)
        _update_project(destination)
        _assert_generated_project(destination, "order-service", "order_service")
        generated_readme = (destination / "README.md").read_text(encoding="utf-8")
        assert "Template update check for order-service." in generated_readme
        _validate_project(destination, "order_service")

    print("Copier template copy and update validated successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
