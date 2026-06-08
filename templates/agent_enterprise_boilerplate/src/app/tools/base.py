from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """返回工具名称。"""

    @abstractmethod
    async def arun(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行工具。"""
