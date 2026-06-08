# OCR 应用

`ocr-app` 是基于 `document-engine` 的可运行命令行应用。它负责读取配置、初始化日志、选择解析模式、调用文档解析引擎，并把最终 Markdown 写入输出目录。

## 职责边界

- 应用层负责 `.env`、settings、logger、bootstrap、CLI 参数、输出目录和异常处理。
- 能力层由 `packages/document_engine` 提供，不反向依赖本应用。

## 快速开始

```bash
uv sync --all-packages --all-extras --group dev
uv run ocr-app path/to/file.pdf
```

指定模式和输出目录：

```bash
uv run ocr-app path/to/file.pdf --mode vector --output-dir output
uv run ocr-app path/to/file.pdf --mode vision --output-dir output
```

## 配置

`.env.example` 由 `src/ocr_app/config/settings.py` 的 `Settings` 字段生成。

```bash
cd apps/ocr_app
uv run python scripts/generate_env_example.py
uv run python scripts/generate_env_example.py --check
```
