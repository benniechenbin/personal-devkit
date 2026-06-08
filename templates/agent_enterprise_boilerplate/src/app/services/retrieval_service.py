from typing import Any, Protocol


class RetrievalService(Protocol):
    async def search(self, query: str) -> list[dict[str, Any]]: ...
