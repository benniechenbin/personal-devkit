from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.container.container import Container
from app.workflows.state import GraphState


def make_executor_node(
    container: Container,
) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def executor_node(
        state: GraphState,
        config: RunnableConfig | None = None,
    ) -> dict[str, Any]:
        del config
        _ = container
        return {
            "output": {
                "status": "completed",
                "processed_steps": len(state.get("plan", [])),
            }
        }

    return executor_node
