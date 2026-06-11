.PHONY: install lock sync-shared check-env-example lint format type type-apps type-packages type-templates type-template-agent type-template-python type-shared type-retrieval test check check-template clean

install:
	uv sync --all-packages --all-extras --group dev

lock:
	uv lock --check

sync-shared:
	uv run python templates/_shared/sync_shared.py --check

check-env-example:
	cd apps/ocr_app && uv run python scripts/generate_env_example.py --check
	cd apps/personal_finance_app && uv run python scripts/generate_env_example.py --check
	cd apps/subtitle_harvester_app && uv run python scripts/generate_env_example.py --check
	cd templates/python_project_boilerplate && uv run python scripts/generate_env_example.py --check
	cd templates/agent_enterprise_boilerplate && uv run python scripts/generate_env_example.py --check

lint:
	uv run ruff check .

format:
	uv run ruff format . --check

type: type-apps type-packages type-templates

type-apps:
	uv run mypy apps/ocr_app/src apps/personal_finance_app/src apps/subtitle_harvester_app/src

type-packages:
	uv run mypy packages/crawl_engine/src packages/document_engine/src packages/analysis_engine/src

type-templates: type-template-agent type-template-python type-shared

type-template-agent:
	uv run mypy templates/agent_enterprise_boilerplate/src

type-template-python:
	uv run mypy templates/python_project_boilerplate/src

type-shared:
	uv run mypy templates/_shared

type-retrieval:
	uv run mypy packages/retrieval_engine/src

test:
	uv run pytest

check: lock sync-shared check-env-example lint format type test

check-template:
	uv run python templates/python_project_boilerplate/scripts/check_copier_template.py

clean:
	uv run python -c "import shutil; from pathlib import Path; names={'.pytest_cache','.mypy_cache','.ruff_cache','htmlcov','dist','build','__pycache__'}; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('*') if p.name in names]; [p.unlink(missing_ok=True) for p in Path('.').rglob('.coverage')]"
