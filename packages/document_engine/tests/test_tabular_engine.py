from pathlib import Path

from document_engine.engines.tabular_engine import TabularEngine


def test_parse_csv():
    engine = TabularEngine()
    csv_path = Path(__file__).parent / "data" / "test_finance.csv"
    fragments = engine.parse(csv_path)

    assert len(fragments) == 1
    assert fragments[0].type == "table"
    assert "Food" in fragments[0].content
    assert "Lunch at KFC" in fragments[0].content


def test_parse_excel():
    engine = TabularEngine()
    excel_path = Path(__file__).parent / "data" / "test_finance.xlsx"
    fragments = engine.parse(excel_path)

    assert len(fragments) == 1
    assert fragments[0].type == "table"
    assert "Food" in fragments[0].content
    assert "50" in fragments[0].content
