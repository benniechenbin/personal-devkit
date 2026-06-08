# services/ocr_engine/math_extractor.py
import logging
import os

logger = logging.getLogger(__name__)


def _load_pix2text():
    try:
        from pix2text import Pix2Text
    except ImportError as exc:
        raise RuntimeError(
            "Pix2Text support requires installing document-engine[formula]."
        ) from exc
    return Pix2Text


class MathExtractor:
    def __init__(self):
        pix2text_cls = _load_pix2text()
        logger.info("正在加载 Pix2Text 公式识别引擎。")
        # 强制使用 CPU 运行，保持沙盒的轻量级特性
        # 启用 mfd (Math Formula Detection) 和 mfr (Math Formula Recognition)
        self.p2t = pix2text_cls.from_config(total_configs={"device": "cpu"})
        logger.info("Pix2Text 公式识别引擎加载完成。")

    def extract_formula_from_image(self, img_path: str) -> str:
        """
        对传入的局部公式截图进行定点爆破，转化为 LaTeX
        """
        if not os.path.exists(img_path):
            logger.warning("找不到公式图像文件: %s", img_path)
            return ""

        try:
            # 核心调用：将图片喂给微型引擎
            # expected_type='formula' 强制引擎将其作为纯公式处理，提高准度
            result = self.p2t.recognize_formula(img_path)

            if not result:
                return ""

            # 包装成标准的 Markdown / Obsidian 行间公式格式
            latex_str = f"\n$$\n{result}\n$$\n"
            return latex_str

        except Exception as e:
            logger.warning("公式解析失败: %s", e)
            return "[公式解析异常]"


# ==========================================
# 🧪 微型数学大脑单点测试
# ==========================================
if __name__ == "__main__":
    import time

    # 【测试准备】请用截图工具，随便截取一个包含分数或积分的数学公式，保存为 tests/formula_test.png
    test_img_path = "tests/formula_test.png"

    if os.path.exists(test_img_path):
        extractor = MathExtractor()

        logger.info("开始解析公式截图: %s", test_img_path)
        start_time = time.time()

        latex_result = extractor.extract_formula_from_image(test_img_path)
        cost_time = time.time() - start_time

        print("\n" + "=" * 40)
        print(f"🎯 LaTeX 翻译完成！(耗时: {cost_time:.2f} 秒)")
        print("=" * 40)
        print(latex_result)
        print("=" * 40)
    else:
        logger.error("请在 tests 目录下放置一张公式截图: %s", test_img_path)
