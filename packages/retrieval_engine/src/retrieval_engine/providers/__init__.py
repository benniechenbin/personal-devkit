"""宿主项目提供的模型集成协议。"""

from rtrieval_engine.providers.base import (
    EmbeddingProvider,
    LLMProvider,
    RerankerProvider,
)

__all__ = ["EmbeddingProvider", "LLMProvider", "RerankerProvider"]
