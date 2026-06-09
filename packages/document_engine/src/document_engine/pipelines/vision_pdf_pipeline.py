import logging
import os

import fitz  # PyMuPDF

from ..components.image_extractor import ImageExtractor
from ..formatters.markdown_formatter import MarkdownFormatter
from ..schema import Fragment

logger = logging.getLogger(__name__)


def _load_paddleocr():
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise RuntimeError(
            "PaddleOCR support requires installing document-engine[vision]."
        ) from exc
    return PaddleOCR


class VisionPdfPipeline:
    _ocr_engine = None

    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.image_extractor = ImageExtractor()
        self.formatter = MarkdownFormatter()

    def get_ocr_engine(self):
        """按需唤醒视觉大脑的单例工厂"""
        if VisionPdfPipeline._ocr_engine is None:
            logger.info("首次触发，正在加载 PaddleOCR。")
            PaddleOCR = _load_paddleocr()
            VisionPdfPipeline._ocr_engine = PaddleOCR(use_angle_cls=True, lang="ch", use_gpu=False)
        return VisionPdfPipeline._ocr_engine

    def process_pdf(self, pdf_path: str) -> list[Fragment]:
        """
        全量视觉解析流：将 PDF 转为图片 -> OCR -> 输出 Fragment 列表
        """
        logger.info("启动全视觉流解析: %s", pdf_path)
        doc = fitz.open(pdf_path)

        # 1. 初始化容器
        fragments = []

        # 2. 遍历页面
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                # 渲染成高精度图片
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                temp_path = os.path.join(self.output_dir, f"temp_vision_p{page_num}.jpg")
                pix.save(temp_path)

                # OCR 提取文本
                text = self.extract_text_from_image(temp_path)

                # 核心：装箱为 Fragment (不再直接拼接字符串)
                frag = Fragment(
                    type="text",
                    y0=float(page_num) * 1000.0,  # 简单模拟坐标，确保排序顺序
                    page_num=page_num,
                    content=text,
                    source="vision",
                )
                fragments.append(frag)

                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        finally:
            doc.close()
            logger.debug("已释放 Vision PDF 句柄。")

        # 返回装满 Fragment 的列表，留给外部的 Assembler 去处理
        return fragments

    def extract_text_from_image(self, image_path: str) -> str:
        """对传入的图片路径进行全量文本 OCR 提取"""
        if not os.path.exists(image_path):
            logger.warning("找不到图像文件: %s", image_path)
            return ""

        try:
            # ⚡ 在这里才真正调用单例
            ocr = self.get_ocr_engine()
            result = ocr.ocr(image_path, cls=True)

            if not result or not result[0]:
                return ""

            extracted_text = ""
            for line in result[0]:
                text, confidence = line[1]
                extracted_text += text + "\n"

            return extracted_text.strip()
        except Exception as e:
            logger.warning("PaddleOCR 解析图片失败: %s", e)
            return ""
