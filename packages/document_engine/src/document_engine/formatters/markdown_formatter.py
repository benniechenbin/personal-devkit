# 原路径：services/ocr_engine/formatters.py
import logging
import re

logger = logging.getLogger(__name__)


class MarkdownFormatter:
    def __init__(self) -> None:
        pass

    def clean_text(self, raw_text: str) -> str:
        """
        第一道工序：清洗 OCR 带来的特殊乱码
        """
        if not raw_text:
            return ""

        # 擦除文本中无意义的空格（匹配汉字之间的空格并消除，保留英文/数字之间的空格）
        cleaned = re.sub(r"\n{3,}", "\n\n", raw_text)

        return cleaned

    def format_to_markdown(self, raw_text: str) -> str:
        """
        总门面：执行纯净的格式化流水线
        """
        logger.debug("启动 Markdown 文本清洗。")
        final_markdown = self.clean_text(raw_text)
        return final_markdown
