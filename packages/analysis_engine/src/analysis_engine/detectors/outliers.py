import pandas as pd
from ..schema import StandardEntry, AnomalyFact, FlowDirection


class OutlierDetector:
    """
    负责检测交易记录中的离群值（大额异常支出）。
    """

    def __init__(self, entries: list[StandardEntry], threshold: float = 2.0):
        """
        参数：
            threshold: 阈值倍数。如果金额超过该分类均值的 threshold 倍，则视为异常。
        """
        self.entries = entries
        self.threshold = threshold
        self.df = self._to_df()

    def _to_df(self) -> pd.DataFrame:
        if not self.entries:
            return pd.DataFrame()

        data = [
            {
                "id": i,
                "amount": e.amount,
                "direction": e.direction.value,
                "category": e.category,
                "description": e.description,
            }
            for i, e in enumerate(self.entries)
        ]
        return pd.DataFrame(data)

    def detect_category_outliers(self) -> list[AnomalyFact]:
        """按分类检测大额开支异常（仅针对流出）"""
        if self.df.empty:
            return []

        anomalies = []

        outflows = self.df[self.df["direction"] == FlowDirection.OUTFLOW.value]
        if outflows.empty:
            return anomalies

        # 按分类计算均值
        category_stats = (
            outflows.groupby("category")["amount"].agg(["mean", "std"]).reset_index()
        )

        # 合并回原表
        merged = outflows.merge(category_stats, on="category")

        # 识别异常：采用 [amount > mean * threshold] 且 [amount > 500] (硬阈值避免小钱报警)
        potential_anomalies = merged[
            (merged["amount"] > merged["mean"] * self.threshold)
            & (merged["amount"] > 500.0)
        ]

        for _, row in potential_anomalies.iterrows():
            entry_idx = row["id"]
            related_entry = self.entries[entry_idx]

            anomalies.append(
                AnomalyFact(
                    type="spike",
                    severity="warning",
                    message=(
                        f"检测到 '{row['category']}' 分类存在异常高额流出："
                        f"{row['amount']} 元（分类均值：{row['mean']:.2f}）"
                    ),
                    related_entries=[related_entry],
                )
            )

        return anomalies
