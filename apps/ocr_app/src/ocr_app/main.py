from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

from document_engine.assembler import DocumentAssembler
from document_engine.formatters.markdown_formatter import MarkdownFormatter
from document_engine.formatters.obsidian_formatter import ObsidianWrapper
from document_engine.pipelines.vector_pdf_pipeline import VectorPdfPipeline
from document_engine.pipelines.vision_pdf_pipeline import VisionPdfPipeline

from ocr_app.config.settings import Settings, get_settings
from ocr_app.core.bootstrap import init_workspace
from ocr_app.observability.logger import logger


def run_pdf_to_markdown(
    pdf_path: Path,
    *,
    mode: str,
    output_dir: Path,
) -> Path:
    if not pdf_path.exists():
        raise FileNotFoundError(f"文件不存在: {pdf_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("系统启动，当前引擎模式: {}", mode.upper())

    engine: VectorPdfPipeline | VisionPdfPipeline
    if mode == "vector":
        vector_pipeline_cls = cast(Any, VectorPdfPipeline)
        engine = cast(VectorPdfPipeline, vector_pipeline_cls(output_dir=str(output_dir)))
    elif mode == "vision":
        vision_pipeline_cls = cast(Any, VisionPdfPipeline)
        engine = cast(VisionPdfPipeline, vision_pipeline_cls(output_dir=str(output_dir)))
    else:
        raise ValueError(f"未知文档解析模式: {mode}")

    fragments = engine.process_pdf(str(pdf_path))
    logger.info("引擎解析完成，共提取 {} 个数据碎片。", len(fragments))

    raw_markdown = DocumentAssembler().assemble(fragments)
    cleaned_text = MarkdownFormatter().format_to_markdown(raw_markdown)
    final_markdown = ObsidianWrapper.inject_yaml_frontmatter(cleaned_text, str(pdf_path))

    output_file = output_dir / f"{pdf_path.stem}_{mode}.md"
    output_file.write_text(final_markdown, encoding="utf-8")
    logger.success("文档流水线执行成功，文件已生成: {}", output_file)
    return output_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 PDF 解析为 Markdown。")
    parser.add_argument("pdf_path", type=Path, help="待解析 PDF 文件路径。")
    parser.add_argument(
        "--mode",
        choices=["vector", "vision"],
        default=None,
        help="解析模式。未指定时使用 settings.doc_processing_mode。",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="输出目录。未指定时使用 settings.output_dir。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app_settings: Settings = init_workspace(get_settings())
    mode = args.mode or app_settings.doc_processing_mode
    output_dir = args.output_dir or app_settings.resolved_output_dir

    try:
        run_pdf_to_markdown(args.pdf_path, mode=mode, output_dir=output_dir)
    except Exception as exc:
        logger.exception("运行失败: {}", exc)
        raise


if __name__ == "__main__":
    main()
