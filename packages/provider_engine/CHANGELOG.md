# Changelog

## 0.1.0

- 新增 `LLMProvider`、`EmbeddingProvider`、`RerankerProvider` 协议。
- 新增 OpenAI Chat provider，提供 `complete()` 和 `acomplete()`。
- 新增 OpenAI Embedding provider，提供 `embed_query()`、`embed_documents()` 及异步版本。
- 新增 `ModelRouter`，支持按用途注册和调用 LLM / Embedding provider。
- 新增 `RetryPolicy`，支持同步和异步重试。
- 新增轻量结构化输出 helper，支持解析为 Pydantic 模型或 JSON dict。
- 新增 provider 错误层，统一封装配置、调用、解析和路由错误。
- OpenAI Chat / Embedding provider 支持 `base_url` 和 `timeout`，方便接入 OpenAI-compatible 网关。
- Provider 调用失败会统一包装为 `ProviderCallError`，配置错误保留为 `ProviderConfigurationError`。
- Chat message 归一化会校验 `role` 和 `content`，并保留 `name` 等扩展字段。
