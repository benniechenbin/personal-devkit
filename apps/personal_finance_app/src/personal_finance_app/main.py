import argparse
import sys
from pathlib import Path

from analysis_engine.synthesis.report_builder import ReportBuilder
from document_engine import DocumentRouter
from loguru import logger
from openai import OpenAI

from personal_finance_app.config import settings
from personal_finance_app.core.banner import show_banner
from personal_finance_app.core.bootstrap import init_workspace


def main() -> None:
    """Main entrypoint for the CLI MVP."""
    init_workspace()
    show_banner("FINANCE ANALYZER")

    parser = argparse.ArgumentParser(description="Personal Finance CLI MVP")
    parser.add_argument("file_path", help="Path to the Excel/CSV bill file")
    args = parser.parse_args()

    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    logger.info(f"Processing file: {file_path.name}")

    # 1. Parsing
    try:
        router = DocumentRouter()
        fragments = router.parse(file_path)
        logger.info(f"Parsed {len(fragments)} document fragments.")
    except Exception as e:
        logger.error(f"Failed to parse document: {e}")
        sys.exit(1)

    # Convert fragments to raw data dictionaries (simple extraction for MVP)
    # The TabularReader outputs a single Fragment with markdown table content.
    # To keep it simple, we should probably bypass the markdown rendering in TabularReader
    # or just use pandas directly here. Since analysis_engine accepts list[dict],
    # and document_engine's TabularReader outputs Markdown, they don't cleanly connect without
    # parsing the markdown back to dict.

    # FOR MVP: We will just read the file directly with pandas here to feed analysis_engine,
    # as document_engine is currently built to output Markdown fragments for LLM context,
    # not structured data for another engine.
    import pandas as pd

    try:
        if file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        raw_data = df.to_dict(orient="records")
        logger.info(f"Loaded {len(raw_data)} raw records.")
    except Exception as e:
        logger.error(f"Failed to load structured data: {e}")
        sys.exit(1)

    # 2. Analysis
    try:
        # 假设常见的账单列名
        mapping = {
            "date": "timestamp",
            "日期": "timestamp",
            "amount": "amount",
            "金额": "amount",
            "direction": "direction",
            "收支": "direction",
            "category": "category",
            "分类": "category",
            "description": "description",
            "描述": "description",
        }
        builder = ReportBuilder(mapping=mapping)
        report = builder.build_report(raw_data)
        logger.info(
            "Generated analysis report with %s metrics and %s anomalies.",
            len(report.metrics),
            len(report.anomalies),
        )
        print("\n" + report.summary_text + "\n")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    # 3. LLM Insights
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY is not set. Skipping LLM insights.")
        return

    logger.info("Requesting optimization suggestions from LLM...")
    try:
        client = OpenAI(api_key=settings.openai_api_key)

        prompt = f"""
        你是一位专业的个人理财助理。请基于以下用户近期的财务数据事实简报，
        给出3条具体、可执行的财务优化建议。如果发现异常开销，请重点关注。

        {report.summary_text}
        """

        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "你是一位专业的理财规划师。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        insights = response.choices[0].message.content
        print("\n### 💡 AI 理财建议\n")
        print(insights)
    except Exception as e:
        logger.error(f"Failed to get LLM insights: {e}")


if __name__ == "__main__":
    main()
