from pathlib import Path

from document_engine.readers.tabular_reader import TabularReader


def test_tabular_reader():
    """测试 TabularReader 功能"""
    reader = TabularReader()
    csv_path = Path(__file__).parent / "data" / "test_finance.csv"
    assert csv_path.exists(), f"测试文件不存在: {csv_path}"
    fragments = reader.parse(csv_path)
    assert len(fragments) == 1
    assert fragments[0].type == "table"
