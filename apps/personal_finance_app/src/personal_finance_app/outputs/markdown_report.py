from pathlib import Path

from loguru import logger


class MarkdownReportGenerator:
    def __init__(self, output_dir: Path = Path("reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, report_data, advice, filename: str = "report.md"):
        """生成 Markdown 格式的报告文件。"""
        output_path = self.output_dir / filename
        # TODO: Format report_data and advice into markdown
        logger.info(f"Markdown report generated at {output_path} (Not implemented)")
        return output_path
