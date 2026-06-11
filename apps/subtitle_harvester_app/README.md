# subtitle-harvester-app

`subtitle-harvester-app` 用于从 TMDb 抓取影视候选元数据，为后续字幕搜索、下载和归档流程提供输入清单。

应用会按年份或月份查询 TMDb discovery 接口，将结果规范化为小型 JSON 载荷，并默认写入 `output/` 目录。

## 功能

- 按年份或月份抓取电影和剧集候选条目。
- 输出 TMDb ID、IMDb ID、标题、原始标题、日期、语言、简介和别名。
- 生成稳定的 UTF-8 JSON，方便下游字幕工具继续处理。
- 同时支持 TMDb v3 API Key 和 TMDb Read Access Token。

## 快速开始

```bash
uv sync --extra dev
cp .env.example .env
```

在 `.env` 中填写 `TMDB_API_KEY` 后运行：

```bash
uv run subtitle-harvester-app --year 2026 --month 6 --media-type all
```

默认输出路径为：

```text
output/media_candidates_<year>_<month>_<media-type>.json
```

## 命令行

```bash
uv run subtitle-harvester-app --help
```

常用示例：

```bash
uv run subtitle-harvester-app --year 2026 --media-type movie
uv run subtitle-harvester-app --year 2026 --month 6 --media-type tv --max-pages 5
uv run subtitle-harvester-app --year 2026 --output output/candidates.json
```

## 配置

`.env.example` 由 `src/subtitle_harvester_app/config/settings.py` 自动生成。

```env
APP_NAME=subtitle-harvester-app
APP_ENV=development
LOG_DIR=logs
OUTPUT_DIR=output
LOG_LEVEL=INFO
TMDB_API_KEY=
TMDB_LANGUAGE=zh-CN
TMDB_REGION=CN
TMDB_MAX_PAGES=3
```

`TMDB_API_KEY` 可以使用：

- TMDb v3 API Key，通过 `api_key` 查询参数发送
- TMDb Read Access Token，通过 `Authorization: Bearer ...` 请求头发送

## 开发

```bash
make install
make env-example
make test
make check
```

常用 Make 目标：

| 命令 | 说明 |
| :--- | :--- |
| `make install` | 安装项目和开发依赖。 |
| `make run` | 使用默认参数运行 CLI。 |
| `make test` | 运行带覆盖率的 pytest。 |
| `make lint` | 运行 Ruff 自动修复和格式化。 |
| `make check` | 运行 Ruff 和 Mypy 检查。 |
| `make env-example` | 根据 settings 重新生成 `.env.example`。 |
| `make check-env-example` | 检查 `.env.example` 是否最新。 |
| `make clean` | 清理本地缓存和构建产物。 |

## 容器

```bash
cp .env.example .env
docker compose run --rm app
```

Compose 服务会把本地 `logs/` 和 `output/` 目录挂载进容器。

## 许可证

MIT
