import argparse
import sys
from pathlib import Path

from loguru import logger

from personal_finance_app.core.banner import show_banner
from personal_finance_app.core.bootstrap import bootstrap
from personal_finance_app.services.finance_report_service import FinanceReportService


def run_cli():
    """CLI 入口函数。"""
    bootstrap()
    show_banner("FINANCE ANALYZER")

    parser = argparse.ArgumentParser(description="Personal Finance CLI 0.2.0")
    parser.add_argument("file_path", help="Path to the Excel/CSV bill file")
    args = parser.parse_args()

    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    logger.info(f"Processing file: {file_path.name}")

    service = FinanceReportService()
    try:
        result = service.generate_full_report(file_path)
        print("\n" + result.report.summary_text + "\n")
        print("### 💡 AI 理财建议\n")
        print(result.advice)

        print(f"\n✅ 报告已归档: {result.report_path}")
        print(f"✅ 数据已存入数据库 (ID: {result.db_run_id})")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_cli()
