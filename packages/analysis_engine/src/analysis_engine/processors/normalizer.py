import logging
from typing import Any, Dict, Optional
from datetime import datetime
import pandas as pd
from ..schema import StandardEntry, FlowDirection

logger = logging.getLogger(__name__)


class DataNormalizer:
    """
    负责将非标准化的原始字典数据映射并转换为统一的 StandardEntry 模型。
    支持自动推断 amount 的正负号来设定 direction。
    """

    def __init__(self, mapping: Optional[Dict[str, str]] = None):
        """
        Args:
            mapping: 字典映射表，格式为 {"原始字段名": "StandardEntry字段名"}
                     StandardEntry字段名支持: timestamp, amount, direction, category, description
        """
        self.mapping = mapping or {
            "时间": "timestamp",
            "date": "timestamp",
            "金额": "amount",
            "amount": "amount",
            "value": "amount",  # 兼容旧配置
            "类型": "direction",
            "type": "direction",
            "direction": "direction",
            "类别": "category",
            "category": "category",
            "描述": "description",
            "description": "description",
        }

    def normalize(self, raw_data: list[dict[str, Any]]) -> list[StandardEntry]:
        """将原始数据列表转换为 StandardEntry 列表"""
        if not raw_data:
            return []

        df = pd.DataFrame(raw_data)

        # 1. 应用字段映射（改名）
        rename_map = {k: v for k, v in self.mapping.items() if k in df.columns}
        df = df.rename(columns=rename_map)

        # 2. 检查必要字段
        required_fields = ["timestamp", "amount", "category"]
        missing = [f for f in required_fields if f not in df.columns]
        if missing:
            logger.error(f"Missing required fields after mapping: {missing}")
            # 过滤掉缺失关键信息的行
            df = df.dropna(subset=[f for f in required_fields if f in df.columns])
            if df.empty:
                return []

        normalized_entries = []
        for _, row in df.iterrows():
            try:
                # 处理日期
                ts = row["timestamp"]
                if isinstance(ts, str):
                    ts = pd.to_datetime(ts).to_pydatetime()
                elif not isinstance(ts, datetime):
                    ts = (
                        datetime.fromtimestamp(ts)
                        if isinstance(ts, (int, float))
                        else datetime.now()
                    )

                # 处理金额与方向
                raw_amount = float(row["amount"])

                # 如果明确提供了 direction 字段，则解析它
                direction_val = str(row.get("direction", "")).lower()
                if direction_val in ["收入", "inflow", "in", "+"]:
                    direction = FlowDirection.INFLOW
                elif direction_val in ["支出", "outflow", "out", "-"]:
                    direction = FlowDirection.OUTFLOW
                elif direction_val in ["转账", "neutral"]:
                    direction = FlowDirection.NEUTRAL
                else:
                    # 默认兼容常见“全为正数的支出账单”：
                    # 没有 direction 时，负数和正数都默认视为 OUTFLOW。
                    # 如需区分收入，请由 app 层显式传入 direction 字段或映射规则。
                    if raw_amount < 0:
                        direction = FlowDirection.OUTFLOW
                    elif raw_amount > 0 and direction_val == "":
                        # 为了向下兼容和常见信用卡账单：正数默认当支出
                        # 如果需要不同逻辑，应当由应用层传入 mapping / rules
                        direction = FlowDirection.OUTFLOW
                    else:
                        direction = FlowDirection.NEUTRAL

                abs_amount = abs(raw_amount)

                entry = StandardEntry(
                    timestamp=ts,
                    amount=abs_amount,
                    direction=direction,
                    category=str(row.get("category", "Uncategorized")),
                    description=str(row.get("description", ""))
                    if pd.notna(row.get("description"))
                    else None,
                    tags=list(row.get("tags", [])),
                    meta={
                        k: v
                        for k, v in row.to_dict().items()
                        if k
                        not in [
                            "timestamp",
                            "amount",
                            "value",
                            "direction",
                            "category",
                            "description",
                            "tags",
                        ]
                    },
                )
                normalized_entries.append(entry)
            except Exception as e:
                logger.warning(f"Failed to normalize row: {row.to_dict()}. Error: {e}")
                continue

        return normalized_entries
