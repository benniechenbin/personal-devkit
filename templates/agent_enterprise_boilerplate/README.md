# Agent Enterprise Boilerplate

A lightweight, evolvable Python skeleton for personal agent assistants that can
grow into a commercial or enterprise application without starting with a heavy
runtime.

## Architecture

```text
main.py
  -> lifecycle.build_app()
  -> Container
  -> AgentRunner
  -> BaseWorkflow / LangGraphWorkflow
  -> LangGraph nodes
  -> Tools / Services
```

The default planner and executor nodes only prove the workflow connection. They
do not call an LLM or contain project-specific business logic.

## Quick Start

```bash
uv sync --extra dev
uv run agent-app
uv run pytest
uv run ruff check .
uv run mypy .
```

Copy `.env.example` to `.env` only when a real provider-backed service needs
credentials. The default skeleton run does not require an API key.
`.env.example` is generated from `app.config.settings.Settings`:

```bash
make env-example
```

Run the one-shot CLI container with:

```bash
docker compose run --rm app
```

## Package Boundaries

- `lifecycle.py`: lightweight bootstrap and optional lifespan hook
- `container/`: explicit resource assembly
- `runtime/`: one-run control context and runner
- `workflows/`: workflow abstraction and LangGraph implementation
- `workflows/nodes/`: LangGraph node adapters
- `agents/`: future standalone agent capabilities
- `resources/`: packaged runtime prompts and other static resources
- `tools/`: tool interfaces and registry
- `services/`: external service interfaces
- `observability/`: logging and future observability extension points

## Shared Template Maintenance

This template keeps runtime code self-contained. Monorepo-level shared template
sources live under `templates/_shared/` only to reduce maintenance drift; they
are synced into this package instead of imported at runtime.

```bash
uv run python templates/_shared/sync_shared.py --check
uv run python templates/_shared/sync_shared.py
```
