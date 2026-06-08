# Python 通用项目模板

一个由 Copier 驱动的轻量 Python 通用项目底座。模板不包含 Agent、Runtime、Workflow、LangGraph，适合快速创建普通库、CLI、脚本服务或轻量后端项目。

当前仓库的默认参考实现使用：

```text
项目名：python-project-boilerplate
包名：python_project_boilerplate
源码：src/python_project_boilerplate
```

Copier 会根据输入的 `project_name` 自动计算合法 Python 包名：

```text
project_name=order-service
package_name=order_service
源码目录=src/order_service
```

## 使用 Copier

从当前模板仓库生成项目：

```bash
uv tool run copier copy --vcs-ref HEAD . ../order-service
```

输入项目名后，Copier 会生成 `.copier-answers.yml`。该文件必须提交，且不要手工修改。
`project_name` 决定包目录，首次生成后应保持稳定；`copier update` 用于同步模板演进，不用于项目重命名。

模板发布 Git tag 后，生成项目可同步模板更新：

```bash
uv tool run copier update
```

开发期间需要同步模板仓库最新提交时：

```bash
uv tool run copier update --vcs-ref HEAD
```

## 核心特性

- **动态包路径**：`src/<package_name>`，不再固定为 `src/app`。
- **持续同步**：生成项目携带 `.copier-answers.yml`，支持 `copier update`。
- **uv 驱动**：统一依赖安装、锁文件和运行命令。
- **通用配置**：使用 `pydantic-settings` 加载默认值、环境变量和本地 `.env`。
- **轻量日志**：使用 `loguru` 提供控制台、文件日志和自定义文件输出。
- **质量检查**：内置 `ruff`、`mypy`、`pytest` 和覆盖率配置。
- **提交前校验**：提供 `pre-commit` 基础格式、安全和类型检查钩子。
- **容器化**：提供多阶段 `Dockerfile`、`docker-compose.yml` 和 `.dockerignore`。
- **工程闭环**：提供 Makefile、CI、多阶段 Dockerfile 和环境变量示例生成脚本。

## 模板结构

```text
copier.yml                       Copier 问题、派生变量与模板配置
template/                        生成项目的唯一 Copier 模板源
template/src/{{ package_name }}/ 动态 Python 包目录
src/python_project_boilerplate/  默认参考实现
scripts/check_copier_template.py 模板生成与运行校验
```

共享维护源位于 monorepo 的 `templates/_shared/`。这些文件只用于维护时同步，Copier 生成的新项目仍然携带本地源码，不依赖 monorepo 的 `package/common` 或 `_shared` 目录。

```bash
uv run python templates/_shared/sync_shared.py --check
uv run python templates/_shared/sync_shared.py
```

## 快速开始

```bash
uv sync --extra dev
make env-example
cp .env.example .env
make run
```

两个等价的默认参考实现入口：

```bash
uv run base-app
uv run python -m python_project_boilerplate.main
```

## 开发命令

| 命令 | 说明 |
| :--- | :--- |
| `make install` | 安装项目依赖和开发工具 |
| `make run` | 通过 `base-app` 启动应用 |
| `make test` | 运行测试并输出覆盖率 |
| `make lint` | 自动修复 Ruff 问题并格式化代码 |
| `make check` | 运行 Ruff、格式和 Mypy 检查 |
| `make lock` | 检查 `uv.lock` 是否与项目配置一致 |
| `make env-example` | 根据 `Settings` 字段生成 `.env.example` |
| `make check-env-example` | 检查 `.env.example` 是否需要重新生成 |
| `make check-template` | 生成自定义项目并验证动态包路径与命令闭环 |
| `make clean` | 清理缓存和构建产物 |

## 配置

默认参考实现配置：

```env
# 应用名称，用于启动横幅和日志标识。
APP_NAME=python-project-boilerplate
# 运行环境，可选值：development、test、production。
APP_ENV=development
# 日志目录。相对路径会基于项目根目录解析。
LOG_DIR=logs
# 日志级别，可选值：DEBUG、INFO、WARNING、ERROR、CRITICAL。
LOG_LEVEL=INFO
```

`.env.example` 由 `Settings` 字段生成，生成脚本不读取本地 `.env`，secret-like 字段会生成空值。

```bash
make env-example
make check-env-example
```

## 提交前检查

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

## 容器运行

```bash
cp .env.example .env
docker compose up --build
```

只构建镜像：

```bash
docker build .
```

Dockerfile 使用 Debian slim 系列镜像，降低 Alpine/musl 在 Python 依赖编译时的兼容风险。CI 会构建镜像并启动容器做冒烟检查。

## CI 安全检查

CI 使用 TruffleHog OSS 扫描已验证和未知状态的 secret。`.env`、日志、缓存和构建产物不会被 Git 跟踪，也不会进入 Docker build context。

## 模板边界

本模板是 Python Base Template，不包含 Agent、Runtime、Workflow、LangGraph。
如需多智能体或 LangGraph 编排，请使用 `agent_enterprise_boilerplate`。

## 许可证

MIT
