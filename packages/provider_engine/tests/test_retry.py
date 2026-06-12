from __future__ import annotations

import pytest
from provider_engine.errors import ProviderCallError
from provider_engine.policies import RetryPolicy


def test_retry_policy_retries_until_success():
    calls = {"count": 0}
    policy = RetryPolicy(max_attempts=3, initial_delay_seconds=0)

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("temporary")
        return "ok"

    assert policy.run(flaky) == "ok"
    assert calls["count"] == 2


def test_retry_policy_raises_provider_error_after_attempts():
    policy = RetryPolicy(max_attempts=2, initial_delay_seconds=0)

    with pytest.raises(ProviderCallError):
        policy.run(lambda: (_ for _ in ()).throw(RuntimeError("boom")))
