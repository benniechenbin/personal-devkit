import logging

from document_engine.assembler import DocumentAssembler
from document_engine.engines.docx_engine import DocxEngine
from document_engine.engines.tabular_engine import TabularEngine
from document_engine.engines.vector_engine import VectorPipeline
from document_engine.router import DocumentRouter
from document_engine.schema import Fragment

__all__ = [
    "DocumentAssembler",
    "Fragment",
    "TabularEngine",
    "VectorPipeline",
    "DocumentRouter",
    "DocxEngine",
]
__version__ = "0.2.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())
