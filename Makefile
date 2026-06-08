.PHONY: install lock sync-shared check-env-example lint format type type-retrieval test check check-template clean

install:
	uv sync --all-packages --all-extras --group dev

lock:
	uv lock --check

sync-shared:
	uv run python templates/_shared/sync_shared.py --check

check-env-example:
	cd templates/python_project_boilerplate && uv run python scripts/generate_env_example.py --check
	cd templates/agent_enterprise_boilerplate && uv run python scripts/generate_env_example.py --check

lint:
	uv run ruff check .

format:
	uv run ruff format . --check

type:
	uv run mypy templates/agent_enterprise_boilerplate/src templates/python_project_boilerplate/src templates/_shared

type-retrieval:
	uv run mypy package/retrieval_engine/src

test:
	uv run pytest

check: lock sync-shared check-env-example lint format type test

check-template:
	uv run python templates/python_project_boilerplate/scripts/check_copier_template.py

clean:
	uv run python -c "import shutil; from pathlib import Path; names={'.pytest_cache','.mypy_cache','.ruff_cache','htmlcov','dist','build','__pycache__'}; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('*') if p.name in names]; [p.unlink(missing_ok=True) for p in Path('.').rglob('.coverage')]"
