import logging

from document_engine.assembler import DocumentAssembler
from document_engine.router import DocumentRouter
from document_engine.schema import Fragment

__all__ = [
    "DocumentAssembler",
    "DocumentRouter",
    "Fragment",
]

__version__ = "0.2.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())
