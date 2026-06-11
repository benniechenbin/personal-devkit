from datetime import datetime
from pathlib import Path

from loguru import logger


class MarkdownReportGenerator:
    def __init__(self, output_dir: Path = Path("data/reports")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, month: str, summary_text: str, advice: str) -> Path:
        """生成并保存 Markdown 格式的报告文件。"""
        filename = f"{month}-finance-report.md"
        output_path = self.output_dir / filename

        content = f"""# 财务分析报告 ({month})

生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 1. 数据分析事实简报

{summary_text}

## 2. AI 理财建议

{advice}

---
*本报告由个人财务应用 0.2.0 自动生成，作为后续分析的上下文语料。*
"""

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Markdown report archived at {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate markdown report: {e}")
            raise
