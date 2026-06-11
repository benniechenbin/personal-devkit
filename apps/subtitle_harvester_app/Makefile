.PHONY: install run test lint check lock env-example check-env-example clean

install:
	uv sync --extra dev

run:
	uv run subtitle-harvester-app

test:
	uv run pytest

lint:
	uv run ruff check . --fix
	uv run ruff format .

check:
	uv run ruff check .
	uv run ruff format . --check
	uv run mypy src

lock:
	uv lock --check

env-example:
	uv run python scripts/generate_env_example.py

check-env-example:
	uv run python scripts/generate_env_example.py --check

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
