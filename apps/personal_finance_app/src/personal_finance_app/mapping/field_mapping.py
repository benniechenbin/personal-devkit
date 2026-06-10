from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, field_validator

DEFAULT_MAPPING = {
    "date": "timestamp",
    "日期": "timestamp",
    "amount": "amount",
    "金额": "amount",
    "总额": "amount",
    "direction": "direction",
    "收支": "direction",
    "类型": "direction",
    "category": "category",
    "分类": "category",
    "类别": "category",
    "description": "description",
    "描述": "description",
}


class TransactionRecord(BaseModel):
    """标准化交易记录。"""

    timestamp: str
    amount: float
    category: str = "未分类"
    description: str = ""
    direction: Literal["in", "out", "neutral"] = "out"

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: Any) -> float:
        """处理空值并转换为 float。"""
        if pd.isna(v):
            return 0.0
        return float(v)

    @field_validator("direction", mode="before")
    @classmethod
    def normalize_direction(cls, v: Any) -> str:
        """将中英文方向统一为 in / out / neutral。"""
        if v is None or pd.isna(v):
            return "out"

        value = str(v).strip().lower()

        if value in {"in", "income", "inflow", "收入", "入账", "+"}:
            return "in"

        if value in {"out", "expense", "outflow", "支出", "出账", "-"}:
            return "out"

        if value in {"neutral", "transfer", "转账", "内部转账", "还款"}:
            return "neutral"

        return "out"
