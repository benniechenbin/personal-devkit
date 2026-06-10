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
    direction: Literal["in", "out"] = "out"

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, v: Any) -> float:
        """处理空值并转换为 float。"""
        if pd.isna(v):
            return 0.0
        return float(v)


def normalize_record(record: dict) -> TransactionRecord:
    """将原始记录转换为标准化字段格式。"""

    def get_val(keys, default=None):
        for k in keys:
            v = record.get(k)
            if v is not None and not (isinstance(v, float) and pd.isna(v)):
                return v
        return default

    data = {
        "timestamp": str(get_val(["timestamp", "日期", "date"], default="")),
        "amount": get_val(["amount", "金额", "总额"]),
        "category": get_val(["category", "分类", "类别"], default="未分类"),
        "description": get_val(["description", "描述", "说明"], default=""),
        "direction": get_val(["direction", "收支", "类型"], default="out"),
    }
    return TransactionRecord(**data)
