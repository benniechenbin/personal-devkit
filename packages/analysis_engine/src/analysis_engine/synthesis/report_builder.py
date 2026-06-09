from datetime import datetime
from typing import Any, Dict, List, Optional
from ..schema import AnalysisReport, MetricFact, AnomalyFact
from ..processors.normalizer import DataNormalizer
from ..calculators.timeseries import TimeseriesCalculator
from ..detectors.outliers import OutlierDetector


class ReportBuilder:
    """
    分析引擎的主协调器，负责从原始数据构建完整的 AnalysisReport。
    """

    def __init__(self, mapping: Optional[Dict[str, str]] = None):
        self.normalizer = DataNormalizer(mapping=mapping)

    def build_report(self, raw_data: list[dict[str, Any]]) -> AnalysisReport:
        # 1. 标准化
        entries = self.normalizer.normalize(raw_data)
        if not entries:
            now = datetime.now()
            return AnalysisReport(period_start=now, period_end=now, raw_entry_count=0)

        # 排序
        entries.sort(key=lambda x: x.timestamp)
        start_date = entries[0].timestamp
        end_date = entries[-1].timestamp

        # 2. 计算指标
        calc = TimeseriesCalculator(entries)
        metrics = []
        metrics.append(calc.get_total_inflow())
        metrics.append(calc.get_total_outflow())
        metrics.append(calc.get_net_flow())
        metrics.extend(calc.get_monthly_summary())
        metrics.extend(calc.get_mom_change())

        # 3. 检测异常
        detector = OutlierDetector(entries)
        anomalies = detector.detect_category_outliers()

        # 4. 生成文本摘要 (作为 LLM 的主要语料)
        summary = self._generate_briefing(metrics, anomalies)

        return AnalysisReport(
            period_start=start_date,
            period_end=end_date,
            metrics=metrics,
            anomalies=anomalies,
            summary_text=summary,
            raw_entry_count=len(entries),
        )

    def _generate_briefing(
        self, metrics: List[MetricFact], anomalies: List[AnomalyFact]
    ) -> str:
        """生成面向 LLM 的事实简报"""
        lines = ["### 数据分析事实简报", ""]

        # 核心指标
        total_inflow = next(
            (m for f in metrics if (m := f).name == "Total Inflow"), None
        )
        total_outflow = next(
            (m for f in metrics if (m := f).name == "Total Outflow"), None
        )
        net_flow = next((m for f in metrics if (m := f).name == "Net Flow"), None)

        if total_inflow and total_inflow.value > 0:
            lines.append(
                f"- **总流入**: {total_inflow.value} {total_inflow.unit or ''}"
            )
        if total_outflow:
            lines.append(
                f"- **总流出**: {total_outflow.value} {total_outflow.unit or ''}"
            )
        if net_flow:
            lines.append(f"- **净流量**: {net_flow.value} {net_flow.unit or ''}")

        mom = [m for m in metrics if m.name == "Monthly Outflow MoM Change"]
        if mom:
            latest_mom = mom[-1]
            direction = "上升" if latest_mom.change_rate > 0 else "下降"
            lines.append(
                f"- **流出近期趋势**: 较上个周期{direction} {abs(latest_mom.change_rate * 100):.1f}%"
            )

        # 异常点
        if anomalies:
            lines.append("\n### 异常与特别关注")
            for a in anomalies:
                lines.append(f"- [{a.severity.upper()}] {a.message}")

        return "\n".join(lines)
