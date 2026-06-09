from document_engine.pipelines.vector_pdf_pipeline import VectorPdfPipeline
from document_engine.pipelines.vision_pdf_pipeline import VisionPdfPipeline
from document_engine.readers.docx_reader import DocxReader
from document_engine.readers.tabular_reader import TabularReader


def test_new_public_paths_are_importable() -> None:
    assert VectorPdfPipeline is not None
    assert VisionPdfPipeline is not None
    assert DocxReader is not None
    assert TabularReader is not None
