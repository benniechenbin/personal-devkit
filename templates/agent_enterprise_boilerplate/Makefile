.PHONY: run test lint check clean install env-example check-env-example env-example-check

install:
	uv sync --extra dev

run:
	uv run agent-app

test:
	uv run pytest tests/ -v

env-example:
	uv run python scripts/generate_env_example.py

check-env-example:
	uv run python scripts/generate_env_example.py --check

env-example-check: check-env-example

lint:
	uv run ruff check .
	uv run ruff format .

check:
	$(MAKE) check-env-example
	uv run ruff check .
	uv run ruff format . --check
	uv run mypy src/ scripts/

clean:
	rm -rf `find . -name __pycache__`
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
