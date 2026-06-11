from pathlib import Path
from typing import Any, cast

import pandas as pd
from loguru import logger


class LedgerImporter:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load_data(self) -> list[dict[str, Any]]:
        """从 CSV 或 Excel 文件加载账单数据。"""
        try:
            suffix = self.file_path.suffix.lower()
            if suffix == ".csv":
                df = pd.read_csv(self.file_path)
            else:
                # 针对当前“个人预算.xlsx”模板，尝试使用特定页签和表头行
                try:
                    df = pd.read_excel(self.file_path, sheet_name="交易", header=1)
                except ValueError:
                    logger.warning(
                        f"Sheet '交易' not found in {self.file_path.name}, "
                        "falling back to the first sheet."
                    )
                    df = pd.read_excel(self.file_path)

            # 过滤占位行 / 空行
            if "日期" in df.columns and "总额" in df.columns:
                df = df.dropna(subset=["日期", "总额"])
            elif "date" in df.columns and "amount" in df.columns:
                df = df.dropna(subset=["date", "amount"])

            records = cast(list[dict[str, Any]], df.to_dict(orient="records"))
            logger.info(f"Loaded {len(records)} raw records from {self.file_path.name}.")
            return records
        except Exception as e:
            logger.error(f"Failed to load structured data from {self.file_path}: {e}")
            raise
