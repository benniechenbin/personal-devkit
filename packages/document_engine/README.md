# 文档解析引擎

`document-engine` 是可复用的文档解析能力包，负责把 PDF 等文档解析为结构化碎片，并提供 Markdown/Obsidian 格式化能力。

这个包只保留能力层代码，不读取 `.env`，不持有应用级 settings/bootstrap，也不决定运行模式。调用方负责选择引擎、传入输入文件和输出目录，并处理日志、异常和落盘。

包内日志使用 Python 标准库 `logging.getLogger(__name__)`，不依赖 `loguru`，也不配置 handler。应用层可以按自己的需要接管标准 logging，或桥接到 `loguru`。

基础安装只包含矢量 PDF 解析所需的轻量依赖。公式识别和视觉 OCR 属于可选能力：

```bash
uv add "document-engine[formula]"        # Pix2Text 公式识别
uv add "document-engine[vision]"         # PaddleOCR 视觉 OCR
uv add "document-engine[formula,vision]" # 完整 OCR 应用能力
```

## 能力边界

- `engines/`：文档解析引擎，例如矢量 PDF 解析和视觉 OCR 解析。
- `components/`：图片、表格、公式、遮罩等局部提取组件。
- `assembler.py`：按页码和物理坐标重组解析碎片。
- `formatters/`：Markdown 清洗与 Obsidian frontmatter 包装。
- `schema.py`：文档碎片等基础数据结构。

## 调用示例

```python
from document_engine.assembler import DocumentAssembler
from document_engine.engines.vector_engine import VectorPipeline
from document_engine.formatters.markdown_formatter import MarkdownFormatter
from document_engine.formatters.obsidian_formatter import ObsidianWrapper


engine = VectorPipeline(output_dir="output")
fragments = engine.process_pdf("example.pdf")

raw_markdown = DocumentAssembler().assemble(fragments)
cleaned = MarkdownFormatter().format_to_markdown(raw_markdown)
final_markdown = ObsidianWrapper.inject_yaml_frontmatter(cleaned, "example.pdf")
```

## 与应用层的关系

完整可运行的 OCR 命令行应用位于 `apps/ocr_app`。依赖方向必须保持为：

```text
apps/ocr_app
  -> packages/document_engine
```

不要在 `document_engine` 中 import `ocr_app.config.settings` 或 `ocr_app.observability.logger`。如果后续需要更细的进度反馈，可以由 app 注入 callback，或者在 app 层消费 package 抛出的结构化结果。

## 本地检查

```bash
uv run pytest packages/document_engine/tests
uv run ruff check packages/document_engine
uv run ruff format packages/document_engine --check
```
