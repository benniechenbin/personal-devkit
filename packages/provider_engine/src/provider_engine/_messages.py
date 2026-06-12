from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from provider_engine.errors import ProviderConfigurationError
from provider_engine.protocols import MessageLike
from provider_engine.schema import ChatMessage


def normalize_messages(messages: Sequence[MessageLike]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for message in messages:
        payload = message.to_provider_dict() if isinstance(message, ChatMessage) else dict(message)

        if "role" not in payload or "content" not in payload:
            raise ProviderConfigurationError("message must contain role and content")

        normalized.append(payload)
    return normalized
