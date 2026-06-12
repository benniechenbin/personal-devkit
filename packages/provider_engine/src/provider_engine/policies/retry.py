from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from provider_engine.errors import ProviderCallError, ProviderConfigurationError

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.25
    backoff_factor: float = 2.0
    retry_exceptions: tuple[type[BaseException], ...] = (Exception,)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds must be >= 0")
        if self.backoff_factor < 1:
            raise ValueError("backoff_factor must be >= 1")

    def run(self, func: Callable[[], T]) -> T:
        delay = self.initial_delay_seconds
        last_error: BaseException | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return func()
            except self.retry_exceptions as exc:
                if isinstance(exc, ProviderConfigurationError):
                    raise
                last_error = exc
                if attempt >= self.max_attempts:
                    break
                if delay > 0:
                    time.sleep(delay)
                delay *= self.backoff_factor

        raise ProviderCallError("provider call failed after retries") from last_error

    async def arun(self, func: Callable[[], Awaitable[T]]) -> T:
        delay = self.initial_delay_seconds
        last_error: BaseException | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await func()
            except self.retry_exceptions as exc:
                if isinstance(exc, ProviderConfigurationError):
                    raise
                last_error = exc
                if attempt >= self.max_attempts:
                    break
                if delay > 0:
                    await asyncio.sleep(delay)
                delay *= self.backoff_factor

        raise ProviderCallError("provider call failed after retries") from last_error
