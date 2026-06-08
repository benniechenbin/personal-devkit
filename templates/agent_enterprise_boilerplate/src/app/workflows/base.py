from abc import ABC, abstractmethod
from typing import Any

from app.runtime.context import RunContext


class BaseWorkflow(ABC):
    @abstractmethod
    async def arun(
        self,
        input_data: dict[str, Any],
        context: RunContext,
    ) -> dict[str, Any]:
        """执行一次工作流。"""
