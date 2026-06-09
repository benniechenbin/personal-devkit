import fitz  # PyMuPDF


class MaskManager:
    def __init__(self, threshold: float = 0.5) -> None:
        self.masks: list[tuple[tuple[float, float, float, float], str]] = []
        self.threshold = threshold

    def add(self, bbox: tuple[float, float, float, float], source_type: str) -> None:
        """添加一个涂白结界，并记录是由谁产生的"""
        self.masks.append((bbox, source_type))

    def is_masked(self, target_bbox: tuple[float, float, float, float]) -> bool:
        """精准判断目标区域是否被现有的结界遮挡"""
        r1 = fitz.Rect(target_bbox)
        for mask_bbox, _source_type in self.masks:
            r2 = fitz.Rect(mask_bbox)
            intersect = r1.intersect(r2)
            if r1.get_area() > 0 and (intersect.get_area() / r1.get_area()) > self.threshold:
                return True
        return False
