# 项目模板说明

`templates/` 放的是可复用的项目模板和模板维护辅助文件。这里的模板用于创建新项目或维护参考实现，不作为运行时公共包被业务项目 import。

## 模板选择

| 模板 | 适合用途 | 主要特点 |
| :--- | :--- | :--- |
| `python_project_boilerplate` | 普通 Python 项目、CLI、脚本服务、轻量后端、可复用库 | Copier 驱动，支持动态包名、`.copier-answers.yml`、`copier update`、基础 settings/logger/bootstrap、质量检查和容器化 |
| `agent_enterprise_boilerplate` | Agent 应用、LangGraph 工作流、未来可能扩展为企业级应用的助手系统 | 固定 `src/app` 结构，内置 lifecycle、container、runtime、workflow、tool、service、observability 边界 |

选择时可以简单判断：

- 只需要一个干净的 Python 项目底座，选 `python_project_boilerplate`。
- 需要 Agent 运行生命周期、LangGraph 节点、工具注册和服务边界，选 `agent_enterprise_boilerplate`。
- 不确定时先选 `python_project_boilerplate`，等业务确实需要 Agent 编排后再迁移或参考 agent 模板补结构。

## `python_project_boilerplate`

这是当前真正 Copier 化的模板。它的 `template/` 目录是生成新项目的唯一模板源，`src/python_project_boilerplate/` 是默认参考实现。

典型生成方式：

```bash
cd templates/python_project_boilerplate
uv tool run copier copy --vcs-ref HEAD . ../../order-service
```

生成的新项目会携带自己的 `settings`、`logger`、`bootstrap`、`banner` 等基础代码，因此可以脱离本 monorepo 独立运行。

## `agent_enterprise_boilerplate`

这是 Agent 应用参考模板，目前不是 Copier 模板。它强调清晰的运行边界，而不是一开始就把所有企业级能力做满。

核心结构：

- `lifecycle.py`：应用创建、启动和关闭入口。
- `container/`：集中组装运行资源。
- `runtime/`：一次性运行上下文和 runner。
- `workflows/`：工作流抽象和 LangGraph 实现。
- `tools/`、`services/`：工具与外部服务边界。
- `observability/`：日志和未来观测扩展点。

## `_shared`

`templates/_shared/` 是模板维护侧的共享源头，不是运行时公共包。

它的目标是减少模板之间完全相同文件的维护漂移。例如当前的 `core/banner.py` 由 `_shared` 维护，再同步到：

- `templates/python_project_boilerplate/src/python_project_boilerplate/core/banner.py`
- `templates/python_project_boilerplate/template/src/{{ package_name }}/core/banner.py`
- `templates/agent_enterprise_boilerplate/src/app/core/banner.py`

这样做有两个好处：

- monorepo 内维护时有一个共享源头。
- Copier 创建的新项目仍然自包含，不依赖 `templates/_shared` 或未来的 `package/common`。

## 同步共享文件

检查共享源和模板副本是否一致：

```bash
uv run python templates/_shared/sync_shared.py --check
```

把共享源同步到各模板副本：

```bash
uv run python templates/_shared/sync_shared.py
```

根目录 `make check` 和 CI 会执行 `--check`，所以如果改了 `_shared` 但忘记同步，检查会失败。

## 维护原则

- 生成项目必须保持自包含，不能运行时依赖本 monorepo 的模板目录。
- `settings`、`logger`、`bootstrap` 优先保留在模板或应用内，因为它们会随项目类型分化。
- 只有足够稳定、低耦合、几乎完全相同的文件，才放入 `_shared`。
- 如果未来需要真正的运行时公共能力，应单独设计 `package/common`，并谨慎评估它对 Copier 生成项目独立性的影响。
