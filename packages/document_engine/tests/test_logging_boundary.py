from pathlib import Path


def test_document_engine_does_not_import_loguru() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src" / "document_engine"
    offenders = []

    for path in source_root.rglob("*.py"):
        content = path.read_text(encoding="utf-8")
        if "loguru" in content:
            offenders.append(path.relative_to(source_root))

    assert offenders == []
