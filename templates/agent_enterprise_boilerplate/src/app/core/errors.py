class AgentApplicationError(RuntimeError):
    """应用级异常基类。"""


class WorkflowExecutionError(AgentApplicationError):
    """工作流无法完成时抛出的异常。"""
