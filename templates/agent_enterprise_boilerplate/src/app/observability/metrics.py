from typing import Protocol


class Metrics(Protocol):
    """未来指标实现的扩展接口。"""

    def increment(self, name: str, value: int = 1) -> None: ...
