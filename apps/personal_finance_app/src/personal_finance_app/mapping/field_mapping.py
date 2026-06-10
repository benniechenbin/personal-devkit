import pandas as pd

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


def normalize_record(record: dict) -> dict:
    """将原始记录转换为标准化字段格式。"""

    def get_val(keys, default=None):
        for k in keys:
            v = record.get(k)
            if v is not None and not (isinstance(v, float) and pd.isna(v)):
                return v
        return default

    return {
        "timestamp": get_val(["timestamp", "日期", "date"]),
        "amount": get_val(["amount", "金额", "总额"]),
        "category": get_val(["category", "分类", "类别"], default="未分类"),
        "description": get_val(["description", "描述", "说明"], default=""),
        "direction": get_val(["direction", "收支", "类型"], default="out"),
    }
