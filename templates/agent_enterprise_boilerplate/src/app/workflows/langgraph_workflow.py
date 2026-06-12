from typing import Any

from langgraph.graph import END, START, StateGraph

from app.container.container import Container
from app.observability.context import RunContext
from app.workflows.base import BaseWorkflow
from app.workflows.nodes.executor_node import make_executor_node
from app.workflows.nodes.planner_node import make_planner_node
from app.workflows.state import GraphState


class LangGraphWorkflow(BaseWorkflow):
    def __init__(self, container: Container) -> None:
        self.container = container
        self.app = self._compile()

    def _compile(self) -> Any:
        graph = StateGraph(GraphState)
        graph.add_node("planner", make_planner_node(self.container))
        graph.add_node("executor", make_executor_node(self.container))
        graph.add_edge(START, "planner")
        graph.add_edge("planner", "executor")
        graph.add_edge("executor", END)
        return graph.compile()

    async def arun(
        self,
        input_data: dict[str, Any],
        context: RunContext,
    ) -> dict[str, Any]:
        initial_state: GraphState = {"input": str(input_data.get("input", ""))}
        config = {
            "configurable": {"request_id": context.request_id},
            "metadata": {**context.metadata, "request_id": context.request_id},
        }
        result = await self.app.ainvoke(initial_state, config=config)
        return dict(result)
