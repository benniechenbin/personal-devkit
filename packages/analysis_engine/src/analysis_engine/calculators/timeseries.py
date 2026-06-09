import pandas as pd
from typing import List
from ..schema import StandardEntry, MetricFact, FlowDirection


class TimeseriesCalculator:
    """
    负责对 StandardEntry 列表进行时序聚合计算。
    """

    def __init__(self, entries: List[StandardEntry]):
        self.entries = entries
        self.df = self._to_df()

    def _to_df(self) -> pd.DataFrame:
        if not self.entries:
            return pd.DataFrame()

        data = [
            {
                "timestamp": e.timestamp,
                "amount": e.amount,
                "signed_value": e.signed_value,
                "direction": e.direction.value,
                "category": e.category,
            }
            for e in self.entries
        ]
        df = pd.DataFrame(data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    def get_total_inflow(self) -> MetricFact:
        """计算总流入"""
        if self.df.empty:
            return MetricFact(name="Total Inflow", value=0.0)
        total = self.df[self.df["direction"] == FlowDirection.INFLOW.value][
            "amount"
        ].sum()
        return MetricFact(name="Total Inflow", value=float(total), unit="元")

    def get_total_outflow(self) -> MetricFact:
        """计算总流出"""
        if self.df.empty:
            return MetricFact(name="Total Outflow", value=0.0)
        total = self.df[self.df["direction"] == FlowDirection.OUTFLOW.value][
            "amount"
        ].sum()
        return MetricFact(name="Total Outflow", value=float(total), unit="元")

    def get_net_flow(self) -> MetricFact:
        """计算净流量 (流入 - 流出)"""
        if self.df.empty:
            return MetricFact(name="Net Flow", value=0.0)
        total = self.df["signed_value"].sum()
        return MetricFact(name="Net Flow", value=float(total), unit="元")

    def get_monthly_summary(self) -> List[MetricFact]:
        """按月和分类进行汇总 (仅针对流出，通常花销分析更关注流出)"""
        if self.df.empty:
            return []

        outflows = self.df[self.df["direction"] == FlowDirection.OUTFLOW.value]
        if outflows.empty:
            return []

        # 按月份和分类分组
        monthly = (
            outflows.groupby([outflows["timestamp"].dt.to_period("M"), "category"])[
                "amount"
            ]
            .sum()
            .reset_index()
        )

        facts = []
        for _, row in monthly.iterrows():
            facts.append(
                MetricFact(
                    name=f"Monthly Category Outflow: {row['category']}",
                    value=float(row["amount"]),
                    unit="元",
                    description=f"Outflow for {row['category']} in {row['timestamp']}",
                )
            )
        return facts

    def get_mom_change(self) -> List[MetricFact]:
        """计算月度流出环比变化"""
        if self.df.empty:
            return []

        outflows = self.df[self.df["direction"] == FlowDirection.OUTFLOW.value]
        if outflows.empty:
            return []

        monthly_total = (
            outflows.groupby(outflows["timestamp"].dt.to_period("M"))["amount"]
            .sum()
            .sort_index()
        )
        if len(monthly_total) < 2:
            return []

        mom = monthly_total.pct_change()

        facts = []
        for period, change in mom.items():
            if pd.isna(change):
                continue
            facts.append(
                MetricFact(
                    name="Monthly Outflow MoM Change",
                    value=float(monthly_total[period]),
                    change_rate=float(change),
                    unit="元",
                    description=f"Month-over-Month outflow change for {period}",
                )
            )
        return facts
