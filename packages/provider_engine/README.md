# provider-engine

`provider-engine` 是一个克制的外部模型能力适配包，用来统一封装 LLM、Embedding、Reranker 等 provider 的协议、实现、重试、模型路由和结构化输出。

它的定位不是 agent runtime，也不是业务流水线框架。它只处理“如何稳定调用外部模型能力”这件事。

## 设计原则

- **独立于业务包**：`retrieval_engine`、`document_engine`、`analysis_engine` 不需要依赖本包。
- **协议优先**：业务包可以保留自己的 `Protocol`，应用层按需注入 `provider_engine` 的实现。
- **克制实现**：第一版只覆盖 LLM、Embedding、模型路由、重试和结构化输出。
- **供应商可替换**：OpenAI 只是第一批适配，后续可以增加 Anthropic、Ollama、vLLM、本地模型等实现。

推荐依赖方向：

```text
apps / agent layer
  -> provider_engine
  -> retrieval_engine / document_engine / analysis_engine

retrieval_engine / document_engine / analysis_engine
  不强依赖 provider_engine
```

## 安装

本地 monorepo 使用：

```bash
uv sync --all-packages
```

如果需要 OpenAI provider：

```bash
uv sync --all-packages --extra openai
```

或在外部项目中安装：

```bash
pip install "provider-engine[openai]"
```

## LLM 调用

```python
from provider_engine.llms import OpenAIChatProvider

llm = OpenAIChatProvider(
    model="gpt-4.1-mini",
    base_url=None,  # 可替换为 OpenAI-compatible 网关地址
    timeout=30.0,
)

text = llm.complete([
    {"role": "system", "content": "你是一个简洁的助手。"},
    {"role": "user", "content": "用一句话解释 RAG。"},
])
```

`complete()` 返回字符串，方便直接适配现有 `retrieval_engine` 的 `LLMProvider` 协议。

## Embedding 调用

```python
from provider_engine.embeddings import OpenAIEmbeddingProvider

embedding = OpenAIEmbeddingProvider(model="text-embedding-3-small")

query_vector = embedding.embed_query("知识库检索")
doc_vectors = embedding.embed_documents(["第一段文本", "第二段文本"])
```

`embed_query()` 和 `embed_documents()` 的形状也兼容常见检索包协议。

当前 OpenAI provider 面向 OpenAI SDK/API。若未来接入 OpenAI-compatible 本地服务或专用本地模型，可新增对应 provider 实现。

## 模型路由

```python
from provider_engine.routing import ModelRouter

router = ModelRouter()
router.register_llm("planner", llm, model="gpt-4.1")
router.register_llm("cheap", llm, model="gpt-4.1-mini")
router.register_embedding("default", embedding)

plan = router.complete("planner", [{"role": "user", "content": "生成执行计划"}])
vector = router.embed_query("default", "查询文本")
```

模型路由适合多智能体场景：planner、critic、writer、extractor 可以用不同模型和参数。

## 结构化输出

```python
from pydantic import BaseModel
from provider_engine.structured import structured_complete

class Plan(BaseModel):
    steps: list[str]

plan = structured_complete(
    llm,
    [{"role": "user", "content": "输出 JSON：三步学习计划"}],
    Plan,
)
```

结构化输出会把模型返回内容解析为 Pydantic 模型。第一版只做轻量解析和校验，不内置复杂 JSON 修复器。

如果传入 Pydantic 模型，会执行字段校验；如果传入 `dict` schema，当前只保证返回内容能解析为 JSON dict，不执行完整 JSON Schema 校验。

## 重试策略

```python
from provider_engine.policies import RetryPolicy

policy = RetryPolicy(max_attempts=3, initial_delay_seconds=0.5)
result = policy.run(lambda: llm.complete(messages))
```

OpenAI provider 也可以直接传入 `retry_policy`。

`InMemoryRateLimiter` 是进程内轻量限流器，适合单进程应用和本地 agent 编排；它不适合多进程或分布式限流。

## 边界

本包第一版不包含：

- agent 编排
- DAG / pipeline 执行器
- 数据库 checkpoint
- 完整 observability
- OCR / speech / vision provider

这些能力可以在未来根据真实项目需求逐步增加。
