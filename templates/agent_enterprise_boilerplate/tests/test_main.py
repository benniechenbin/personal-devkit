import asyncio
from dataclasses import dataclass
from typing import Any

import pytest
from app import main as main_module


def test_main_async_delegates_to_runner(monkeypatch) -> None:
    inputs: list[str] = []

    class StubRunner:
        async def arun(self, input_data: str) -> dict[str, Any]:
            inputs.append(input_data)
            return {"status": "completed"}

    @dataclass
    class StubApp:
        runner: StubRunner

    monkeypatch.setattr(main_module, "build_app", lambda: StubApp(runner=StubRunner()))

    exit_code = asyncio.run(main_module.main_async())

    assert inputs == ["Create a simple plan."]
    assert exit_code == 0


def test_main_async_returns_nonzero_for_failed_result(monkeypatch) -> None:
    class StubRunner:
        async def arun(self, input_data: str) -> dict[str, Any]:
            del input_data
            return {"status": "failed", "error": "workflow failed"}

    @dataclass
    class StubApp:
        runner: StubRunner

    monkeypatch.setattr(main_module, "build_app", lambda: StubApp(runner=StubRunner()))

    exit_code = asyncio.run(main_module.main_async())

    assert exit_code == 1


def test_main_exits_nonzero_when_run_fails(monkeypatch) -> None:
    async def failing_main_async() -> int:
        return 1

    monkeypatch.setattr(main_module, "main_async", failing_main_async)

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()

    assert exc_info.value.code == 1
