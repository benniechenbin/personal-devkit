import logging
import os
import tempfile

import fitz  # PyMuPDF

from ..components.image_extractor import ImageExtractor
from ..components.mask_manager import MaskManager
from ..components.math_extractor import MathExtractor
from ..components.table_extractor import TableExtractor
from ..formatters.markdown_formatter import MarkdownFormatter
from ..schema import Fragment

logger = logging.getLogger(__name__)


class VectorPdfPipeline:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.table_extractor = TableExtractor()
        self.image_extractor = ImageExtractor(output_dir)
        self.formatter = MarkdownFormatter()
        self.math_extractor = None

    def _is_math_block(self, block):
        """⚡ 密度探测雷达"""
        if block.get("type") != 0:
            return False

        math_font_keywords = ["Math", "Symbol", "CMSY", "CMMI", "CMEX"]
        math_symbols = [
            "±",
            "√",
            "∑",
            "∫",
            "≠",
            "≈",
            "≤",
            "≥",
            "α",
            "β",
            "π",
            "θ",
            "△",
            "∈",
            "∪",
            "∩",
        ]

        total_chars = 0
        math_font_chars = 0
        math_symbol_count = 0

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "")
                font = span.get("font", "")
                chars_len = len(text.strip())
                total_chars += chars_len

                if any(mf.lower() in font.lower() for mf in math_font_keywords):
                    math_font_chars += chars_len
                for sym in math_symbols:
                    math_symbol_count += text.count(sym)

        if total_chars == 0:
            return False

        math_density = (math_font_chars + math_symbol_count * 2) / total_chars

        return math_density > 0.3

    # ==========================================
    # 🧩 组件调度 (完全基于 Block 和 MaskManager)
    # ==========================================
    def _process_tables(self, page, page_elements: list[Fragment], mask_manager: MaskManager):
        tables = page.find_tables()
        if tables and tables.tables:
            for idx, tab in enumerate(tables.tables):
                raw_data = tab.extract()
                if raw_data:
                    # 未来升级 Stitcher 时，只改这里即可
                    tab_md = self.table_extractor.render_markdown(raw_data, idx + 1)
                    page_elements.append(
                        Fragment(type="table", y0=tab.bbox[1], content=tab_md, bbox=tab.bbox)
                    )
                    mask_manager.add(tab.bbox, "table")

    def _process_images(
        self,
        doc,
        page,
        page_num,
        pdf_name,
        page_elements: list[Fragment],
        mask_manager: MaskManager,
    ):
        images_info = self.image_extractor.extract_images_from_page(doc, page, page_num, pdf_name)

        for img in images_info:
            page_elements.append(
                Fragment(
                    type="image",
                    y0=img["bbox"][1],
                    content=img["content"],
                    bbox=img["bbox"],
                )
            )

            if img["area_ratio"] < 0.5:
                mask_manager.add(img["bbox"], "image")
            else:
                logger.debug("检测到全页背景图或水印，放行其底部正文提取。")

    def _process_math(self, page, page_elements: list[Fragment], mask_manager: MaskManager):
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            if self._is_math_block(block):
                bbox = block["bbox"]
                if not mask_manager.is_masked(bbox):
                    if self.math_extractor is None:
                        self.math_extractor = MathExtractor()

                    crop_rect = fitz.Rect(bbox) + (-3, -3, 3, 3)

                    # ⚡ 安全升级：使用 tempfile 生成唯一的临时文件，防止并发碰撞
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_img:
                        temp_formula_path = temp_img.name

                    try:
                        page.get_pixmap(clip=crop_rect, matrix=fitz.Matrix(3.0, 3.0)).save(
                            temp_formula_path
                        )
                        latex_md = self.math_extractor.extract_formula_from_image(temp_formula_path)

                        if latex_md and "[公式解析异常]" not in latex_md:
                            page_elements.append(
                                Fragment(
                                    type="math",
                                    y0=crop_rect.y0,
                                    content=latex_md,
                                    bbox=crop_rect,
                                )
                            )
                            mask_manager.add(crop_rect, "math")
                    finally:
                        if os.path.exists(temp_formula_path):
                            os.remove(temp_formula_path)

    def _process_text(self, page, page_elements: list[Fragment], mask_manager: MaskManager) -> int:
        blocks = page.get_text("blocks")
        vector_text_count = 0
        for b in blocks:
            block_bbox = b[:4]
            block_text = b[4].strip()
            if b[6] == 0 and block_text and not mask_manager.is_masked(block_bbox):
                page_elements.append(
                    Fragment(
                        type="text",
                        y0=block_bbox[1],
                        content=block_text,
                        bbox=block_bbox,
                    )
                )
                vector_text_count += len(block_text)
        return vector_text_count

    # ==========================================
    # 🚀 主流程调度器
    # ==========================================
    def process_pdf(self, pdf_path: str) -> list[Fragment]:
        """
        纯粹的碎片生产者：不再负责拼接字符串，只负责产出 Fragment 列表。
        """
        logger.info("开始全局解析文档: %s", pdf_path)
        pdf_name = os.path.basename(pdf_path).replace(".pdf", "")
        doc = fitz.open(pdf_path)
        all_fragments = []  # 存储全文档的所有碎片

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                logger.debug("正在解析第 %s/%s 页。", page_num + 1, len(doc))

                # 每一页的碎片临时容器
                page_elements: list[Fragment] = []
                mask_manager = MaskManager(threshold=0.5)

                self._process_tables(page, page_elements, mask_manager)
                self._process_images(doc, page, page_num, pdf_name, page_elements, mask_manager)
                self._process_math(page, page_elements, mask_manager)
                self._process_text(page, page_elements, mask_manager)

                # 增加页码信息 (这一步很重要，Assembler 需要它)
                for frag in page_elements:
                    frag.page_num = page_num

                all_fragments.extend(page_elements)

        finally:
            doc.close()
            logger.debug("已释放 PDF 句柄。")

        return all_fragments  # 引擎彻底解脱，只返回碎片


if __name__ == "__main__":
    import os

    # 设定测试文件路径（基于在项目根目录运行的假设）
    test_pdf = "tests/mvp_test.pdf"

    print("\n" + "=" * 50)
    logging.basicConfig(level=logging.INFO)
    logger.info("启动 VectorPdfPipeline 引擎级独立测试。")
    print("=" * 50 + "\n")

    if os.path.exists(test_pdf):
        # 实例化引擎（默认输出到项目根目录的 output 文件夹）
        pipeline = VectorPdfPipeline(output_dir="output")

        try:
            result_path = pipeline.process_pdf(test_pdf)
            print("\n" + "=" * 50)
            logger.info("引擎级冒烟测试通过。")
            logger.info("最终输出的 Markdown 产物位置: %s", result_path)
            print("=" * 50 + "\n")
        except Exception as e:
            logger.exception("测试过程中发生运行时异常: %s", e)
            import traceback

            traceback.print_exc()
    else:
        logger.warning("找不到测试文件: %s", test_pdf)
        logger.info("提示：请确保你是在项目根目录下执行测试，且 tests/ 目录中存在 mvp_test.pdf。")
