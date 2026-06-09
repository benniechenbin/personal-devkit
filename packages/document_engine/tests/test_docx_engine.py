from pathlib import Path

from document_engine.engines.docx_engine import DocxEngine
from document_engine.readers.docx_reader import DocxReader


def test_docx_engine_compat():
    """测试旧路径兼容性"""
    engine = DocxEngine()
    docx_path = Path(__file__).parent / "data" / "test.docx"
    if docx_path.exists():
        fragments = engine.parse(docx_path)
        assert len(fragments) >= 1


def test_docx_reader():
    """测试新推荐路径"""
    reader = DocxReader()
    docx_path = Path(__file__).parent / "data" / "test.docx"
    if docx_path.exists():
        fragments = reader.parse(docx_path)
        assert len(fragments) >= 1
