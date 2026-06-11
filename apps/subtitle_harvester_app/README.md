# subtitle-harvester-app

Harvest movie and TV metadata candidates from TMDb for subtitle collection workflows.

The app queries TMDb discovery endpoints for a year or month, normalizes the results into a small JSON payload, and writes the candidate list to `output/` by default.

## Features

- Fetch movie and TV candidates by year or month.
- Include TMDb IDs, IMDb IDs, titles, original titles, dates, languages, overviews, and aliases.
- Write deterministic UTF-8 JSON output for downstream subtitle tooling.
- Support either a TMDb v3 API key or a TMDb Read Access Token.

## Quick Start

```bash
uv sync --extra dev
cp .env.example .env
```

Set `TMDB_API_KEY` in `.env`, then run:

```bash
uv run subtitle-harvester-app --year 2026 --month 6 --media-type all
```

The default output path is:

```text
output/media_candidates_<year>_<month>_<media-type>.json
```

## CLI

```bash
uv run subtitle-harvester-app --help
```

Common examples:

```bash
uv run subtitle-harvester-app --year 2026 --media-type movie
uv run subtitle-harvester-app --year 2026 --month 6 --media-type tv --max-pages 5
uv run subtitle-harvester-app --year 2026 --output output/candidates.json
```

## Configuration

`.env.example` is generated from `src/subtitle_harvester_app/config/settings.py`.

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

`TMDB_API_KEY` can be either:

- a TMDb v3 API key, sent as the `api_key` query parameter
- a TMDb Read Access Token, sent as `Authorization: Bearer ...`

## Development

```bash
make install
make env-example
make test
make check
```

Useful Make targets:

| Command | Description |
| :--- | :--- |
| `make install` | Install project and development dependencies. |
| `make run` | Run the CLI with default arguments. |
| `make test` | Run pytest with coverage. |
| `make lint` | Run Ruff fixes and formatting. |
| `make check` | Run Ruff and Mypy checks. |
| `make env-example` | Regenerate `.env.example` from settings. |
| `make check-env-example` | Check whether `.env.example` is up to date. |
| `make clean` | Remove local caches and build artifacts. |

## Docker

```bash
cp .env.example .env
docker compose run --rm app
```

The compose service mounts local `logs/` and `output/` directories into the container.

## License

MIT
