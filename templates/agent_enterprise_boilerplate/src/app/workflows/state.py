from typing import TypedDict


class WorkflowOutput(TypedDict):
    status: str
    processed_steps: int


class GraphState(TypedDict, total=False):
    input: str
    plan: list[str]
    output: WorkflowOutput
