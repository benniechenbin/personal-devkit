# 智能体企业应用模板

一个轻量、可演进的 Python Agent 应用骨架。它适合从个人助手、内部自动化工具开始，逐步扩展到商业化或企业级应用，而不需要一开始就引入沉重的运行时框架。

## 架构

```text
main.py
  -> lifecycle.build_app()
  -> Container
  -> AgentRunner
  -> BaseWorkflow / LangGraphWorkflow
  -> LangGraph nodes
  -> Tools / Services
```

默认的 planner 和 executor 节点只用于证明工作流链路是通的，不调用真实 LLM，也不包含具体业务逻辑。

## 快速开始

```bash
uv sync --extra dev
uv run agent-app
uv run pytest
uv run ruff check .
uv run mypy .
```

只有在接入真实模型或外部服务时，才需要把 `.env.example` 复制为 `.env` 并填写密钥。默认骨架运行不需要 API key。

`.env.example` 由 `app.config.settings.Settings` 自动生成：

```bash
make env-example
make check-env-example
```

运行一次性 CLI 容器：

```bash
docker compose run --rm app
```

## 包边界

- `lifecycle.py`：轻量启动入口，以及未来可接入 Web 框架 lifespan 的生命周期钩子。
- `container/`：显式组装 settings、workflow、runner、service 等运行资源。
- `runtime/`：一次性运行上下文、事件模型和 runner。
- `workflows/`：工作流抽象与 LangGraph 实现。
- `workflows/nodes/`：LangGraph 节点适配层。
- `agents/`：未来可扩展的独立 agent 能力。
- `resources/`：随包发布的 prompts 等静态运行资源。
- `tools/`：工具接口、工具注册表和示例工具。
- `services/`：外部服务接口边界。
- `observability/`：日志，以及未来 tracing、metrics 等观测能力扩展点。

## 共享模板维护

本模板保持运行时代码自包含。monorepo 层的共享模板源位于 `templates/_shared/`，只用于减少维护漂移；同步时会把共享文件复制进本模板，而不是在运行时从 `_shared` import。

```bash
uv run python templates/_shared/sync_shared.py --check
uv run python templates/_shared/sync_shared.py
```

更多模板选择和 `_shared` 使用说明见 `templates/README.md`。
