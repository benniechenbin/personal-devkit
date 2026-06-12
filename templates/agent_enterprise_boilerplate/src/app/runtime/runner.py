from typing import Any

from app.container.container import Container
from app.observability.context import RunContext
from app.observability.logger import logger, set_trace_id
from app.runtime.events import RunStatus
from app.workflows.base import BaseWorkflow


class AgentRunner:
    """单次工作流执行的轻量控制层。"""

    def __init__(self, workflow: BaseWorkflow, container: Container) -> None:
        self.workflow = workflow
        self.container = container

    async def arun(
        self,
        input_data: str | dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = RunContext.create(metadata=metadata)
        set_trace_id(context.request_id)
        payload = {"input": input_data} if isinstance(input_data, str) else dict(input_data)

        try:
            workflow_result = await self.workflow.arun(payload, context)
        except Exception as exc:
            logger.exception("Workflow execution failed.")
            return {
                "request_id": context.request_id,
                "started_at": context.started_at.isoformat(),
                "status": RunStatus.FAILED.value,
                "error": str(exc),
            }

        return {
            "request_id": context.request_id,
            "started_at": context.started_at.isoformat(),
            "status": RunStatus.COMPLETED.value,
            "result": workflow_result,
        }
