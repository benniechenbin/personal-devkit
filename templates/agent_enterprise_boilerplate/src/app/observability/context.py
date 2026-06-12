import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class RunContext:
    """
    运行上下文，用于在工作流、Agent 和服务之间传递元数据。
    """

    request_id: str
    started_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> "RunContext":
        return cls(
            request_id=request_id or uuid.uuid4().hex,
            started_at=datetime.now(UTC),
            metadata=dict(metadata or {}),
        )
