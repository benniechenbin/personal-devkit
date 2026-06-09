from datetime import datetime
from enum import StrEnum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FlowDirection(StrEnum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"
    NEUTRAL = "neutral"


class StandardEntry(BaseModel):
    """最基础的结构化条目模型。

    amount 始终表示绝对值。
    direction 表示数值方向。
    signed_value 用于聚合净变化。
    """

    timestamp: datetime
    amount: float
    category: str
    direction: FlowDirection = FlowDirection.OUTFLOW
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

    @property
    def signed_value(self) -> float:
        if self.direction == FlowDirection.INFLOW:
            return abs(self.amount)
        if self.direction == FlowDirection.OUTFLOW:
            return -abs(self.amount)
        return self.amount


class MetricFact(BaseModel):
    """计算出的确定性事实指标"""

    name: str
    value: Any
    unit: Optional[str] = None
    change_rate: Optional[float] = None  # 环比或同比变化率
    description: Optional[str] = None


class AnomalyFact(BaseModel):
    """检测出的异常事实"""

    type: str  # e.g., "spike", "trend_deviation", "new_subscription"
    severity: str  # e.g., "info", "warning", "critical"
    message: str
    related_entries: List[StandardEntry] = Field(default_factory=list)


class AnalysisReport(BaseModel):
    """最终交付给 LLM 或 UI 的分析报告容器"""

    period_start: datetime
    period_end: datetime
    metrics: List[MetricFact] = Field(default_factory=list)
    anomalies: List[AnomalyFact] = Field(default_factory=list)
    summary_text: Optional[str] = None  # 确定性生成的文本摘要
    raw_entry_count: int = 0
