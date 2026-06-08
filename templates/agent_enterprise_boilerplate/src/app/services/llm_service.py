from typing import Protocol


class LLMService(Protocol):
    async def complete(self, prompt: str) -> str: ...
