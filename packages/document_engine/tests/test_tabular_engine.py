from pathlib import Path

from document_engine.engines.tabular_engine import TabularEngine
from document_engine.readers.tabular_reader import TabularReader


def test_tabular_engine_compat():
    """测试旧路径兼容性"""
    engine = TabularEngine()
    csv_path = Path(__file__).parent / "data" / "test_finance.csv"
    if csv_path.exists():
        fragments = engine.parse(csv_path)
        assert len(fragments) == 1
        assert fragments[0].type == "table"


def test_tabular_reader():
    """测试新推荐路径"""
    reader = TabularReader()
    csv_path = Path(__file__).parent / "data" / "test_finance.csv"
    if csv_path.exists():
        fragments = reader.parse(csv_path)
        assert len(fragments) == 1
        assert fragments[0].type == "table"
