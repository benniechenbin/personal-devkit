from typing import Any

from app.tools.base import BaseTool


class SearchTool(BaseTool):
    """项目专用搜索实现的占位工具。"""

    @property
    def name(self) -> str:
        return "search"

    async def arun(self, input_data: dict[str, Any]) -> dict[str, Any]:
        del input_data
        raise NotImplementedError("Configure a search provider before using SearchTool.")
