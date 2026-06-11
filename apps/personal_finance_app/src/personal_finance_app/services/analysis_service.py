from typing import Any

from analysis_engine.synthesis.report_builder import ReportBuilder
from loguru import logger

from personal_finance_app.mapping.field_mapping import DEFAULT_MAPPING


class AnalysisService:
    def __init__(self, mapping: dict[str, str] | None = None):
        self.mapping = mapping or DEFAULT_MAPPING
        self.builder = ReportBuilder(mapping=self.mapping)

    def analyze(self, raw_data: list[dict[str, Any]]):
        """根据原始数据生成分析报告。"""
        try:
            report = self.builder.build_report(raw_data)
            logger.info(
                "已生成分析报告，包含 {} 个指标和 {} 个异常。",
                len(report.metrics),
                len(report.anomalies),
            )
            return report
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
