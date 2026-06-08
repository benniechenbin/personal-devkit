from dataclasses import dataclass
from typing import Any


@dataclass
class Fragment:
    """文档解析的原子单元，记录了数据的出身与位置"""

    type: str
    y0: float
    content: str  # ⚠️ 注意：把没有默认值的 content 提上来
    page_num: int = 0  # 赋予默认值，防止 vector_engine 实例化时报错
    source: str = "vector"  # 默认标记为 vector
    bbox: tuple[float, float, float, float] | None = None
    meta: dict[str, Any] | None = None  # 规范一点，加上 Optional
