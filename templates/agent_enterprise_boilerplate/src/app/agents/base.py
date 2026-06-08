from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """当工作流节点承载能力过重时，用于下沉独立 Agent 能力的扩展点。"""

    @abstractmethod
    async def arun(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """执行一次 Agent 能力调用。"""
