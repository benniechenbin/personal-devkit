from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from personal_finance_app.config import settings
from personal_finance_app.importers.ledger_importer import LedgerImporter
from personal_finance_app.mapping.field_mapping import normalize_record
from personal_finance_app.outputs.markdown_report import MarkdownReportGenerator
from personal_finance_app.services.advisor_service import AdvisorService
from personal_finance_app.services.analysis_service import AnalysisService
from personal_finance_app.storage.sqlite_store import SQLiteStore


@dataclass
class FinanceReportResult:
    source_file: Path
    month: str
    raw_record_count: int
    report: Any
    advice: str
    db_run_id: int | None = None
    report_path: Path | None = None


class FinanceReportService:
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.advisor_service = AdvisorService()
        self.storage = SQLiteStore(db_path=str(settings.resolved_db_path))
        self.report_gen = MarkdownReportGenerator(output_dir=settings.resolved_report_dir)

    def generate_full_report(self, file_path: Path) -> FinanceReportResult:
        """协调完整流程：导入 -> 标准化 -> 分析 -> 建议 -> 持久化 -> 归档。"""
        # 1. 导入
        importer = LedgerImporter(file_path)
        raw_data = importer.load_data()

        # 1.5 标准化
        normalized_data = [normalize_record(rec) for rec in raw_data]
        logger.info(f"已标准化 {len(normalized_data)} 条记录，用于分析和存储。")

        # 2. 分析
        # 分析服务仍然接收字典列表
        report = self.analysis_service.analyze([rec.model_dump() for rec in normalized_data])

        # 提取月份 (YYYY-MM)
        month_str = report.period_start.strftime("%Y-%m")

        # 3. 提取建议和存储所需的数据
        summary_data = self._extract_summary(report)
        categories_data = self._extract_categories(report)

        # 4. 生成建议
        advice = self.advisor_service.get_advice(
            report.summary_text,
            categories=categories_data,
        )

        # 5. 归档为 Markdown
        report_path = self.report_gen.generate(month_str, report.summary_text, advice)

        # 6. 持久化到 SQLite
        db_id = self.storage.save_analysis(
            month=month_str,
            summary=summary_data,
            categories=categories_data,
            raw_records=normalized_data,
            report_path=str(report_path),
        )

        return FinanceReportResult(
            source_file=file_path,
            month=month_str,
            raw_record_count=len(normalized_data),
            report=report,
            advice=advice,
            db_run_id=db_id,
            report_path=report_path,
        )

    def _extract_summary(self, report) -> dict[str, float]:
        """从分析报告中提取核心总计指标。"""
        data = {"total_income": 0.0, "total_expense": 0.0, "net_flow": 0.0}
        for m in report.metrics:
            if m.name == "Total Inflow":
                data["total_income"] = m.value
            elif m.name == "Total Outflow":
                data["total_expense"] = m.value
            elif m.name == "Net Flow":
                data["net_flow"] = m.value
        return data

    def _extract_categories(self, report) -> list[dict[str, Any]]:
        """从分析报告中提取分类支出汇总。"""
        categories = []
        prefix = "Monthly Category Outflow: "
        for m in report.metrics:
            if m.name.startswith(prefix):
                category_name = m.name[len(prefix) :]
                categories.append(
                    {"category": category_name, "direction": "expense", "amount": m.value}
                )
        return categories
