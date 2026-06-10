from loguru import logger


class SQLiteStore:
    def __init__(self, db_path: str = "finance.db"):
        self.db_path = db_path
        # TODO: Initialize database connection and tables
        logger.info(f"SQLite store initialized at {self.db_path}")

    def save_records(self, records):
        """将原始记录保存到数据库中。"""
        # TODO: Implement database persistence
        logger.debug(f"Saving {len(records)} records to database (Not implemented)")
        pass
