"""retrieval_engine 的通用异常定义。"""


class RetrievalEngineError(Exception):
    """所有 retrieval_engine 异常的基类。"""

    pass


class ProviderError(RetrievalEngineError):
    """当 Embedding/LLM/Reranker 提供方发生错误时抛出。"""

    pass


class StorageError(RetrievalEngineError):
    """当存储后端（向量库、图数据库）发生错误时抛出。"""

    pass


class ConfigurationError(RetrievalEngineError):
    """当配置或初始化参数不合法时抛出。"""

    pass
