import fitz  # PyMuPDF


class MaskManager:
    def __init__(self, threshold=0.5):
        self.masks = []
        self.threshold = threshold

    def add(self, bbox: tuple, source_type: str):
        """添加一个涂白结界，并记录是由谁产生的"""
        self.masks.append((bbox, source_type))

    def is_masked(self, target_bbox: tuple) -> bool:
        """精准判断目标区域是否被现有的结界遮挡"""
        r1 = fitz.Rect(target_bbox)
        for mask_bbox, _source_type in self.masks:
            r2 = fitz.Rect(mask_bbox)
            intersect = r1.intersect(r2)
            if r1.get_area() > 0 and (intersect.get_area() / r1.get_area()) > self.threshold:
                return True
        return False
