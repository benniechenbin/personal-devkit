from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from provider_engine._messages import normalize_messages
from provider_engine.errors import ProviderCallError, ProviderConfigurationError
from provider_engine.policies import InMemoryRateLimiter, RetryPolicy
from provider_engine.protocols import MessageLike
from provider_engine.schema import LLMResponse, Usage


class OpenAIChatProvider:
    """OpenAI chat completion provider with retrieval-engine compatible methods."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        client: Any | None = None,
        async_client: Any | None = None,
        retry_policy: RetryPolicy | None = None,
        rate_limiter: InMemoryRateLimiter | None = None,
        default_options: dict[str, Any] | None = None,
    ) -> None:
        self.model = model
        self._client = client
        self._async_client = async_client
        self._api_key = api_key
        self._base_url = base_url
        self._timeout = timeout
        self.retry_policy = retry_policy
        self.rate_limiter = rate_limiter
        self.default_options = dict(default_options or {})

    def complete(self, messages: Sequence[MessageLike], **kwargs: Any) -> str:
        return self.complete_response(messages, **kwargs).content

    async def acomplete(self, messages: Sequence[MessageLike], **kwargs: Any) -> str:
        response = await self.acomplete_response(messages, **kwargs)
        return response.content

    def complete_response(self, messages: Sequence[MessageLike], **kwargs: Any) -> LLMResponse:
        try:
            if self.retry_policy is not None:
                return self.retry_policy.run(lambda: self._complete_once(messages, **kwargs))
            return self._complete_once(messages, **kwargs)
        except (ProviderCallError, ProviderConfigurationError):
            raise
        except Exception as exc:
            raise ProviderCallError("provider chat completion failed") from exc

    async def acomplete_response(
        self,
        messages: Sequence[MessageLike],
        **kwargs: Any,
    ) -> LLMResponse:
        try:
            if self.retry_policy is not None:
                return await self.retry_policy.arun(
                    lambda: self._acomplete_once(messages, **kwargs)
                )
            return await self._acomplete_once(messages, **kwargs)
        except (ProviderCallError, ProviderConfigurationError):
            raise
        except Exception as exc:
            raise ProviderCallError("provider chat completion failed") from exc

    def _complete_once(self, messages: Sequence[MessageLike], **kwargs: Any) -> LLMResponse:
        if self.rate_limiter is not None:
            self.rate_limiter.wait()

        completion = self._get_client().chat.completions.create(
            model=kwargs.pop("model", self.model),
            messages=normalize_messages(messages),
            **self._merged_options(kwargs),
        )
        return self._to_response(completion)

    async def _acomplete_once(
        self,
        messages: Sequence[MessageLike],
        **kwargs: Any,
    ) -> LLMResponse:
        if self.rate_limiter is not None:
            await self.rate_limiter.await_wait()

        completion = await self._get_async_client().chat.completions.create(
            model=kwargs.pop("model", self.model),
            messages=normalize_messages(messages),
            **self._merged_options(kwargs),
        )
        return self._to_response(completion)

    def _merged_options(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        merged = dict(self.default_options)
        merged.update(kwargs)
        return merged

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ProviderConfigurationError(
                    "openai package is required. Install provider-engine[openai]."
                ) from exc
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._client

    def _get_async_client(self) -> Any:
        if self._async_client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as exc:
                raise ProviderConfigurationError(
                    "openai package is required. Install provider-engine[openai]."
                ) from exc
            self._async_client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                timeout=self._timeout,
            )
        return self._async_client

    def _to_response(self, completion: Any) -> LLMResponse:
        choice = completion.choices[0]
        message = choice.message
        usage = self._usage(getattr(completion, "usage", None))
        return LLMResponse(
            content=message.content or "",
            model=getattr(completion, "model", None),
            usage=usage,
            raw=completion,
        )

    def _usage(self, raw_usage: Any | None) -> Usage | None:
        if raw_usage is None:
            return None
        raw = raw_usage.model_dump() if hasattr(raw_usage, "model_dump") else dict(raw_usage)
        return Usage(
            prompt_tokens=raw.get("prompt_tokens"),
            completion_tokens=raw.get("completion_tokens"),
            total_tokens=raw.get("total_tokens"),
            raw=raw,
        )
