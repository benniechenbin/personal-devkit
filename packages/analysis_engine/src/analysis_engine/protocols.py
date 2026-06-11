from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DataDetector(Protocol):
    """异常检测器协议。"""

    def detect(self, data: list[float]) -> list[int]:
        """返回异常值的索引。"""
        ...
