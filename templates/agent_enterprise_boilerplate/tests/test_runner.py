import asyncio
from pathlib import Path
from typing import Any

import pytest
from app.config.enums import AppEnv
from app.config.settings import Settings
from app.container.container import Container
from app.core.bootstrap import shutdown_workspace
from app.lifecycle import App, build_app
from app.observability.context import RunContext
from app.runtime.runner import AgentRunner
from app.workflows.base import BaseWorkflow


@pytest.fixture(autouse=True)
def clean_workspace_state():
    shutdown_workspace()
    yield
    shutdown_workspace()


class FailingWorkflow(BaseWorkflow):
    async def arun(
        self,
        input_data: dict[str, Any],
        context: RunContext,
    ) -> dict[str, Any]:
        del input_data, context
        raise RuntimeError("workflow failed")


def make_test_app(tmp_path: Path) -> App:
    settings = Settings(_env_file=None, app_env=AppEnv.TEST, log_dir=tmp_path)
    return build_app(app_settings=settings)


def test_build_app_creates_runner(tmp_path: Path) -> None:
    app = make_test_app(tmp_path)

    assert app.container is not None
    assert app.runner is not None


def test_runner_execution_returns_unified_result(tmp_path: Path) -> None:
    app = make_test_app(tmp_path)

    result = asyncio.run(app.runner.arun("test"))

    assert isinstance(result, dict)
    assert result["request_id"]
    assert result["status"] == "completed"
    assert result["result"]["output"]["status"] == "completed"


def test_runner_returns_failed_result_for_workflow_error() -> None:
    container = Container.build(app_settings=Settings(_env_file=None))
    runner = AgentRunner(workflow=FailingWorkflow(), container=container)

    result = asyncio.run(runner.arun("test"))

    assert result["status"] == "failed"
    assert result["error"] == "workflow failed"
