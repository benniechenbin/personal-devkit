from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from provider_engine.errors import ProviderCallError, ProviderConfigurationError
from provider_engine.policies import InMemoryRateLimiter, RetryPolicy
from provider_engine.schema import EmbeddingResponse, Usage


class OpenAIEmbeddingProvider:
    """OpenAI embedding provider compatible with retrieval-engine protocols."""

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

    def embed_query(self, text: str, **kwargs: Any) -> list[float]:
        vectors = self.embed_documents([text], **kwargs)
        return vectors[0]

    def embed_documents(self, texts: Sequence[str], **kwargs: Any) -> list[list[float]]:
        return self.embed_response(texts, **kwargs).vectors

    async def aembed_query(self, text: str, **kwargs: Any) -> list[float]:
        vectors = await self.aembed_documents([text], **kwargs)
        return vectors[0]

    async def aembed_documents(self, texts: Sequence[str], **kwargs: Any) -> list[list[float]]:
        response = await self.aembed_response(texts, **kwargs)
        return response.vectors

    def embed_response(self, texts: Sequence[str], **kwargs: Any) -> EmbeddingResponse:
        try:
            if self.retry_policy is not None:
                return self.retry_policy.run(lambda: self._embed_once(texts, **kwargs))
            return self._embed_once(texts, **kwargs)
        except (ProviderCallError, ProviderConfigurationError):
            raise
        except Exception as exc:
            raise ProviderCallError("provider embedding call failed") from exc

    async def aembed_response(self, texts: Sequence[str], **kwargs: Any) -> EmbeddingResponse:
        try:
            if self.retry_policy is not None:
                return await self.retry_policy.arun(lambda: self._aembed_once(texts, **kwargs))
            return await self._aembed_once(texts, **kwargs)
        except (ProviderCallError, ProviderConfigurationError):
            raise
        except Exception as exc:
            raise ProviderCallError("provider embedding call failed") from exc

    def _embed_once(self, texts: Sequence[str], **kwargs: Any) -> EmbeddingResponse:
        if self.rate_limiter is not None:
            self.rate_limiter.wait()

        response = self._get_client().embeddings.create(
            model=kwargs.pop("model", self.model),
            input=list(texts),
            **self._merged_options(kwargs),
        )
        return self._to_response(response)

    async def _aembed_once(self, texts: Sequence[str], **kwargs: Any) -> EmbeddingResponse:
        if self.rate_limiter is not None:
            await self.rate_limiter.await_wait()

        response = await self._get_async_client().embeddings.create(
            model=kwargs.pop("model", self.model),
            input=list(texts),
            **self._merged_options(kwargs),
        )
        return self._to_response(response)

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

    def _to_response(self, response: Any) -> EmbeddingResponse:
        vectors = [list(item.embedding) for item in response.data]
        usage = self._usage(getattr(response, "usage", None))
        return EmbeddingResponse(
            vectors=vectors,
            model=getattr(response, "model", self.model),
            usage=usage,
            raw=response,
        )

    def _usage(self, raw_usage: Any | None) -> Usage | None:
        if raw_usage is None:
            return None
        raw = raw_usage.model_dump() if hasattr(raw_usage, "model_dump") else dict(raw_usage)
        return Usage(
            prompt_tokens=raw.get("prompt_tokens"),
            total_tokens=raw.get("total_tokens"),
            raw=raw,
        )
