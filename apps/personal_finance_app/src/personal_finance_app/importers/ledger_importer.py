from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger


class LedgerImporter:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load_data(self) -> list[dict[str, Any]]:
        """从 CSV 或 Excel 文件加载账单数据。"""
        try:
            if self.file_path.suffix == ".csv":
                df = pd.read_csv(self.file_path)
            else:
                df = pd.read_excel(self.file_path)

            records = df.to_dict(orient="records")
            logger.info(f"Loaded {len(records)} raw records from {self.file_path.name}.")
            return records
        except Exception as e:
            logger.error(f"Failed to load structured data from {self.file_path}: {e}")
            raise
