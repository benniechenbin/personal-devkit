# subtitle-harvester-app

一个基于 Python 通用项目模板生成的轻量 Python 项目。

```text
项目名：subtitle-harvester-app
包名：subtitle_harvester_app
源码：src/subtitle_harvester_app
```

## 快速开始

```bash
uv sync --extra dev
make env-example
cp .env.example .env
make run
```

两个等价入口：

```bash
uv run base-app
uv run python -m subtitle_harvester_app.main
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
| `make clean` | 清理缓存和构建产物 |

## Copier 同步

项目由 Copier 生成，`.copier-answers.yml` 必须提交且不要手工修改。
`project_name` 决定包目录，首次生成后应保持稳定；`copier update` 用于同步模板演进，不用于项目重命名。

同步模板已发布版本：

```bash
uv tool run copier update
```

同步模板仓库最新提交：

```bash
uv tool run copier update --vcs-ref HEAD
```

## 配置

`.env.example` 由 `src/subtitle_harvester_app/config/settings.py` 的 `Settings` 字段生成，脚本不读取本地 `.env`。

```env
APP_NAME=subtitle-harvester-app
APP_ENV=development
LOG_DIR=logs
LOG_LEVEL=INFO
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Dockerfile 使用 Debian slim 系列镜像，CI 会构建镜像、执行密钥扫描，并启动容器做冒烟检查。

## 模板边界

本项目来自 Python 通用项目模板，不包含 Agent、Runtime、Workflow、LangGraph。

## 许可证

MIT
