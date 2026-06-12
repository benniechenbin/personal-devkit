from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: MessageRole | str
    content: str
    name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_provider_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"role": str(self.role), "content": self.content}
        if self.name:
            payload["name"] = self.name
        return payload


class Usage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: str
    model: str | None = None
    usage: Usage | None = None
    raw: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmbeddingResponse(BaseModel):
    vectors: list[list[float]]
    model: str | None = None
    usage: Usage | None = None
    raw: Any | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RerankResult(BaseModel):
    index: int
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
