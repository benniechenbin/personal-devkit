import logging

from document_engine.assembler import DocumentAssembler
from document_engine.schema import Fragment

__all__ = ["DocumentAssembler", "Fragment"]
__version__ = "0.1.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())
