from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, TypeVar, overload

from pydantic import BaseModel, TypeAdapter, ValidationError

from provider_engine.errors import ProviderParseError
from provider_engine.protocols import AsyncLLMProvider, LLMProvider, MessageLike

ModelT = TypeVar("ModelT", bound=BaseModel)

JSON_INSTRUCTION = (
    "Return only valid JSON. Do not include markdown fences, commentary, or extra text."
)


@overload
def structured_complete(
    provider: LLMProvider,
    messages: Sequence[MessageLike],
    output_schema: type[ModelT],
    **kwargs: Any,
) -> ModelT: ...


@overload
def structured_complete(
    provider: LLMProvider,
    messages: Sequence[MessageLike],
    output_schema: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]: ...


def structured_complete(
    provider: LLMProvider,
    messages: Sequence[MessageLike],
    output_schema: type[ModelT] | dict[str, Any],
    **kwargs: Any,
) -> ModelT | dict[str, Any]:
    raw = provider.complete(_with_json_instruction(messages), **kwargs)
    return parse_structured_output(raw, output_schema)


async def astructured_complete(
    provider: AsyncLLMProvider,
    messages: Sequence[MessageLike],
    output_schema: type[ModelT] | dict[str, Any],
    **kwargs: Any,
) -> ModelT | dict[str, Any]:
    raw = await provider.acomplete(_with_json_instruction(messages), **kwargs)
    return parse_structured_output(raw, output_schema)


def parse_structured_output(
    raw: str,
    output_schema: type[ModelT] | dict[str, Any],
) -> ModelT | dict[str, Any]:
    cleaned = _strip_json_fences(raw)
    try:
        if isinstance(output_schema, type) and issubclass(output_schema, BaseModel):
            return output_schema.model_validate_json(cleaned)
        data = json.loads(cleaned)
        return TypeAdapter(dict[str, Any]).validate_python(data)
    except (json.JSONDecodeError, TypeError, ValidationError) as exc:
        raise ProviderParseError("failed to parse structured provider output") from exc


def _with_json_instruction(messages: Sequence[MessageLike]) -> list[MessageLike]:
    return [
        {"role": "system", "content": JSON_INSTRUCTION},
        *messages,
    ]


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text
