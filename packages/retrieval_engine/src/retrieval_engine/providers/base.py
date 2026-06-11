from __future__ import annotations

from retrieval_engine.protocols import EmbeddingProvider as EmbeddingProtocol
from retrieval_engine.protocols import LLMProvider as LLMProtocol
from retrieval_engine.protocols import RerankerProvider as RerankerProtocol

EmbeddingProvider = EmbeddingProtocol
RerankerProvider = RerankerProtocol
LLMProvider = LLMProtocol
