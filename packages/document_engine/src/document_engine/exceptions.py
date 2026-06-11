"""document_engine 的通用异常定义。"""


class DocumentEngineError(Exception):
    """所有 document_engine 异常的基类。"""

    pass


class ReaderError(DocumentEngineError):
    """当结构化读取（docx, xlsx）失败时抛出。"""

    pass


class PipelineError(DocumentEngineError):
    """当复杂处理流水线（PDF/OCR）失败时抛出。"""

    pass


class FormatError(DocumentEngineError):
    """当文本格式化或组装失败时抛出。"""

    pass
