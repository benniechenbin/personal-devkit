import logging
import os

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class ImageExtractor:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir

    def extract_images_from_page(
        self, doc: fitz.Document, page: fitz.Page, page_num: int, pdf_name: str
    ) -> list:
        """
        提取图片，并返回包含 markdown 链接、坐标 bbox 和面积占比的字典列表
        """
        image_list = page.get_images(full=True)
        if not image_list:
            return []
        all_bboxes = [page.get_image_bbox(img) for img in image_list]
        is_tiled = detect_image_tiling(all_bboxes)

        if is_tiled:
            logger.warning(
                "第 %s 页检测到高度碎片化的 CAD 切片长图，当前选择忽略。",
                page_num + 1,
            )
            return []

        page_area = page.rect.width * page.rect.height
        specific_img_dir = os.path.join(self.output_dir, f"{pdf_name}_images")
        if not os.path.exists(specific_img_dir):
            os.makedirs(specific_img_dir, exist_ok=True)
        extracted_images = []

        for img_idx, img in enumerate(image_list):
            try:
                img_bbox = page.get_image_bbox(img)
                pix = page.get_pixmap(clip=img_bbox)

                img_filename = f"doc_p{page_num + 1}_img{img_idx + 1}.png"
                img_filepath = os.path.join(specific_img_dir, img_filename)
                pix.save(img_filepath)

                md_link = f"\n\n![插图 {img_idx + 1}](./{pdf_name}_images/{img_filename})\n\n"

                # 计算面积占比，用于 Pipeline 的防水印判定
                img_rect = fitz.Rect(img_bbox)
                area_ratio = img_rect.get_area() / page_area if page_area > 0 else 0

                extracted_images.append(
                    {"content": md_link, "bbox": img_bbox, "area_ratio": area_ratio}
                )
            except Exception as e:
                logger.warning("图片提取异常，已跳过该图片: %s", e)
                continue

        return extracted_images


def detect_image_tiling(
    image_bboxes: list[fitz.Rect], aspect_ratio_threshold=5.0, stack_threshold=3
) -> bool:
    """
    检测一堆图片包围盒中，是否存在“切片长图”现象。

    :param image_bboxes: 页面上所有图片的 bbox 列表
    :param aspect_ratio_threshold: 长宽比阈值，默认 5.0 (宽度是高度的5倍以上视为条状)
    :param stack_threshold: 连续堆叠的数量阈值，默认 3 (连续3个条状图片堆叠即触发报警)
    """
    if len(image_bboxes) < stack_threshold:
        return False

    # 1. 过滤出所有的“细长条”图片
    strip_rects = []
    for bbox in image_bboxes:
        rect = fitz.Rect(bbox)
        if rect.height == 0:
            continue
        aspect_ratio = rect.width / rect.height
        if aspect_ratio > aspect_ratio_threshold:
            strip_rects.append(rect)

    # 如果细长条数量都不够，直接安全
    if len(strip_rects) < stack_threshold:
        return False

    # 2. 按 Y 轴 (从上到下) 排序
    strip_rects.sort(key=lambda r: r.y0)

    # 3. 寻找连续堆叠
    continuous_stack_count = 1

    for i in range(1, len(strip_rects)):
        prev_rect = strip_rects[i - 1]
        curr_rect = strip_rects[i]

        # 判断条件：
        # 条件一：垂直方向紧密贴合 (y1 距离下一个 y0 小于 2 个单位)
        # 条件二：水平方向宽度几乎一致 (宽度差小于 5 个单位)
        y_gap = abs(curr_rect.y0 - prev_rect.y1)
        width_diff = abs(curr_rect.width - prev_rect.width)

        if y_gap < 2.0 and width_diff < 5.0:
            continuous_stack_count += 1
            # 如果连续堆叠超过阈值，立刻确诊！
            if continuous_stack_count >= stack_threshold:
                return True
        else:
            # 链条断裂，重新计数
            continuous_stack_count = 1

    return False
