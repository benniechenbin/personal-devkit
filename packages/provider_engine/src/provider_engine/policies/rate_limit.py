from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class InMemoryRateLimiter:
    """Small process-local rate limiter for simple provider clients.

    This limiter is not suitable for multi-process or distributed rate limiting.
    """

    min_interval_seconds: float
    _last_call_at: float = field(default=0.0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _async_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        if self.min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be >= 0")

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            remaining = self.min_interval_seconds - (now - self._last_call_at)
            if remaining > 0:
                time.sleep(remaining)
            self._last_call_at = time.monotonic()

    async def await_wait(self) -> None:
        async with self._async_lock:
            now = time.monotonic()
            remaining = self.min_interval_seconds - (now - self._last_call_at)
            if remaining > 0:
                await asyncio.sleep(remaining)
            self._last_call_at = time.monotonic()
