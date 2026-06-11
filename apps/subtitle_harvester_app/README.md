# subtitle-harvester-app

`subtitle-harvester-app` 用于从 TMDb 抓取影视候选元数据，并把新增候选交给后续字幕搜索流程处理。

当前阶段覆盖两条链路：

- TMDb 候选发现：生成 snapshot / batch / state 增量输出。
- SubDL 字幕搜索：通过 Provider / Router / Pipeline 骨架验证 API 型字幕源搜索链路。

## 快速开始

```bash
uv sync --extra dev
cp .env.example .env
```

在 `.env` 中填写 `TMDB_API_KEY` 后运行候选发现：

```bash
uv run subtitle-harvester-app --year 2026 --month 6 --media-type all
```

## 输出结构

默认输出结构：

```text
output/
├── snapshots/
│   └── media_candidates_<period>_<media-type>_<run_id>.snapshot.json
├── batches/
│   └── media_candidates_<period>_<media-type>_<run_id>.batch.json
├── latest/
│   ├── latest_snapshot.json
│   └── latest_batch.json
└── state/
    └── seen_media_candidates.json
```

`snapshot` 保存本次 TMDb 返回的全量结果；`batch` 只保存本次新增候选，供后续字幕搜索阶段使用。

使用 `--no-update-state` 可以只写出 snapshot 和 batch，不更新 `seen_media_candidates.json`，适合 dry-run 检查。

## 命令行

```bash
uv run subtitle-harvester-app --help
```

常用示例：

```bash
uv run subtitle-harvester-app --year 2026 --media-type movie
uv run subtitle-harvester-app --year 2026 --month 6 --media-type tv --max-pages 5
uv run subtitle-harvester-app --year 2026 --month 6 --media-type movie --max-pages 1 --no-update-state
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
SUBDL_API_KEY=
SUBDL_LANGUAGES=ZH,ZH-CN,EN
```

`TMDB_API_KEY` 可以使用：

- TMDb v3 API Key，通过 `api_key` 查询参数发送
- TMDb Read Access Token，通过 `Authorization: Bearer ...` 请求头发送

`SUBDL_API_KEY` 用于 SubDL 字幕搜索；`SUBDL_LANGUAGES` 用逗号分隔多个字幕语言筛选值。

## SubDL 冒烟测试

只验证 SubDL 搜索链路时，不需要配置 `TMDB_API_KEY`：

```bash
uv run python scripts/search_subdl_smoke.py
```

## 收官检查

```bash
uv run pytest
uv run python scripts/generate_env_example.py --check
uv run subtitle-harvester-app --year 2026 --month 6 --media-type movie --max-pages 1 --no-update-state
uv run subtitle-harvester-app --year 2026 --month 6 --media-type movie --max-pages 1
```

第二次非 dry-run 执行同一条件时，batch 应为 0 或明显减少。

## 开发

```bash
make install
make env-example
make test
make check
```

## 容器

```bash
cp .env.example .env
docker compose run --rm app
```

Compose 服务会把本地 `logs/` 和 `output/` 目录挂载进容器。

## 许可证

MIT
