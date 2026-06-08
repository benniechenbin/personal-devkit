.PHONY: install run test lint check lock env-example check-env-example check-template clean

install:
	uv sync --extra dev

run:
	uv run base-app

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

check-template:
	uv run python scripts/check_copier_template.py

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage dist build
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
