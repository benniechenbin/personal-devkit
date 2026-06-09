from pathlib import Path

from document_engine import DocumentRouter


def test_router_csv():
    router = DocumentRouter()
    csv_path = Path(__file__).parent / "data" / "test_finance.csv"
    fragments = router.parse(csv_path)
    assert len(fragments) == 1
    assert fragments[0].type == "table"
