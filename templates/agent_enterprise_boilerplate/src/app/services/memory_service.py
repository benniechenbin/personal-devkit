from typing import Any, Protocol


class MemoryService(Protocol):
    async def load(self, key: str) -> dict[str, Any] | None: ...

    async def save(self, key: str, value: dict[str, Any]) -> None: ...
