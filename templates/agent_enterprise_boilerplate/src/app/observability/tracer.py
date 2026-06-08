from typing import Any, Protocol


class Tracer(Protocol):
    """未来追踪实现的扩展接口。"""

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None: ...
