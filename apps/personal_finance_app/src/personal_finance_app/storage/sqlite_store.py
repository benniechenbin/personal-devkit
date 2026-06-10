import sqlite3
from pathlib import Path

from loguru import logger


class SQLiteStore:
    def __init__(self, db_path: str = "finance.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构。"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            # 1. 历史分析运行记录
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month TEXT NOT NULL,
                    total_income REAL,
                    total_expense REAL,
                    net_flow REAL,
                    budget_amount REAL,
                    report_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. 分类汇总记录
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS category_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    category TEXT,
                    direction TEXT,
                    amount REAL,
                    FOREIGN KEY (run_id) REFERENCES analysis_runs (id)
                )
            """)

            # 3. 详细交易记录
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    timestamp TEXT,
                    category TEXT,
                    direction TEXT,
                    amount REAL,
                    description TEXT,
                    FOREIGN KEY (run_id) REFERENCES analysis_runs (id)
                )
            """)
            conn.commit()
        logger.info(f"SQLite database initialized at {self.db_path}")

    def save_analysis(self, month: str, summary, categories, raw_records, report_path: str):
        """保存一次完整的分析记录到数据库。"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 插入主运行记录
                cursor.execute(
                    """
                    INSERT INTO analysis_runs
                    (month, total_income, total_expense, net_flow, report_path)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        month,
                        summary.get("total_income", 0),
                        summary.get("total_expense", 0),
                        summary.get("net_flow", 0),
                        report_path,
                    ),
                )
                run_id = cursor.lastrowid

                # 插入分类汇总
                for cat in categories:
                    cursor.execute(
                        """
                        INSERT INTO category_summaries (run_id, category, direction, amount)
                        VALUES (?, ?, ?, ?)
                    """,
                        (run_id, cat["category"], cat["direction"], cat["amount"]),
                    )

                # 插入详细交易
                for rec in raw_records:
                    cursor.execute(
                        """
                        INSERT INTO transactions
                        (run_id, timestamp, category, direction, amount, description)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            run_id,
                            str(rec.get("timestamp", "")),
                            rec.get("category", "unknown"),
                            rec.get("direction", "unknown"),
                            rec.get("amount", 0),
                            rec.get("description", ""),
                        ),
                    )

                conn.commit()
                logger.info(f"Successfully saved analysis for {month} (ID: {run_id}) to database.")
                return run_id
        except Exception as e:
            logger.error(f"Failed to save analysis to database: {e}")
            raise
