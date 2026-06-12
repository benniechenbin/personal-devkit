import asyncio

from app.config.settings import Settings
from app.container.container import Container
from app.observability.context import RunContext
from app.workflows.base import BaseWorkflow
from app.workflows.langgraph_workflow import LangGraphWorkflow


def test_langgraph_workflow_completes_planner_and_executor() -> None:
    container = Container.build(app_settings=Settings(_env_file=None))
    workflow = LangGraphWorkflow(container=container)
    context = RunContext.create(request_id="test-request")

    result = asyncio.run(workflow.arun({"input": "test"}, context))

    assert isinstance(workflow, BaseWorkflow)
    assert result["plan"] == ["test"]
    assert result["output"] == {"status": "completed", "processed_steps": 1}
