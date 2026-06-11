import logging
from typing import TYPE_CHECKING, Any

from document_engine.assembler import DocumentAssembler
from document_engine.schema import Fragment

if TYPE_CHECKING:
    from document_engine.router import DocumentRouter

__all__ = [
    "DocumentAssembler",
    "DocumentRouter",
    "Fragment",
]

__version__ = "0.2.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name: str) -> Any:
    if name == "DocumentRouter":
        from document_engine.router import DocumentRouter

        return DocumentRouter
    raise AttributeError(name)
