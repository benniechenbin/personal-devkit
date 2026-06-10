from pathlib import Path

from personal_finance_app.importers.ledger_importer import LedgerImporter
from personal_finance_app.services.advisor_service import AdvisorService
from personal_finance_app.services.analysis_service import AnalysisService


class FinanceReportService:
    def __init__(self):
        self.analysis_service = AnalysisService()
        self.advisor_service = AdvisorService()

    def generate_full_report(self, file_path: Path):
        """协调完整流程：导入 -> 分析 -> 建议。"""
        # 1. Import
        importer = LedgerImporter(file_path)
        raw_data = importer.load_data()

        # 2. Analyze
        report = self.analysis_service.analyze(raw_data)
        print("\n" + report.summary_text + "\n")

        # 3. Advise
        advice = self.advisor_service.get_advice(report.summary_text)
        print("\n### 💡 AI 理财建议\n")
        print(advice)

        return report, advice
