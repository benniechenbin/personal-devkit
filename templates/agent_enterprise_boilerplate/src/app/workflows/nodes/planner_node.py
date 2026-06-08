from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.container.container import Container
from app.workflows.state import GraphState


def make_planner_node(
    container: Container,
) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def planner_node(
        state: GraphState,
        config: RunnableConfig | None = None,
    ) -> dict[str, Any]:
        del config
        _ = container
        request = state.get("input", "")
        return {"plan": [request] if request else []}

    return planner_node
