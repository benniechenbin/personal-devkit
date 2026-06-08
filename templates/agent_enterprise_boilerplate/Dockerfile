FROM ghcr.io/astral-sh/uv:python3.11-alpine AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY README.md ./
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.11-alpine

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV LOG_DIR="/app/logs"

CMD ["agent-app"]
