# 检索 SDK

一个极简的个人检索 SDK，用来复用向量库、知识图谱、聚落检测与召回组件。

这个库只做通用方法抽象，不读取环境变量，不内置 settings/logger/bootstrap，也不绑定具体模型。宿主项目负责提供 embedding、LLM、reranker、切片策略、日志和运行生命周期。

## 能力边界

- `loaders/`：轻量文档加载，例如把 Markdown 文件读成完整 `DocumentChunk`。
- `indexing/`：向量入库编排、图谱抽取编排、增量 source cache、社区检测、社区总结。
- `storage/`：向量库和图数据库适配协议，以及 Qdrant/Neo4j 适配器。
- `retrieval/`：向量召回、词法召回、多路召回、图谱局部召回、图谱语义召回、聚落召回。
- `providers/`：宿主项目需要实现的 embedding、LLM、reranker 协议。
- `domain/`：克制的数据模型，例如 `DocumentChunk`、`GraphEntity`、`GraphRelation`、`BuildReport`。

## 安装

本地开发：

```bash
pip install -e ".[dev]"
```

按需安装可选后端：

```bash
pip install -e ".[qdrant,neo4j,lexical,templates]"
```

## 向量入库与召回

```python
from retrieval_sdk import DocumentChunk
from rtrieval_engine.e.e.e.e.indexing import VectorIndexer
from rtrieval_engine.e.e.e.e.e.retrieval import VectorRetriever
from rtrieval_engine.storage import QdrantVectorStorage


class MyEmbeddingProvider:
    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        # 宿主项目接入自己的 embedding 模型
        return [0.0] * 768


documents = [
    DocumentChunk(
        page_content="项目风险评估需要结合文档证据和图谱线索。",
        metadata={"source": "risk.md"},
    )
]

embedding = MyEmbeddingProvider()
storage = QdrantVectorStorage(
    collection_name="knowledge",
    vector_size=768,
    path="./.qdrant",
)

VectorIndexer(storage=storage, embedding_provider=embedding).replace_documents(
    documents
)
results = VectorRetriever(
    storage=storage,
    embedding_provider=embedding,
).search("风险评估", top_k=5)
```

## 图谱构建

```python
from retrieval_sdk import DocumentChunk
from rtrieval_engine.indexing import GraphExtractor, GraphIndexer
from rtrieval_engine.storage import Neo4jGraphWriter


class MyLLMProvider:
    def complete(self, messages, **kwargs):
        # 宿主项目接入自己的 LLM
        return '{"entities": [], "relationships": []}'


writer = Neo4jGraphWriter(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    embedding_provider=None,
)

indexer = GraphIndexer(
    extractor=GraphExtractor(llm_provider=MyLLMProvider()),
    writer=writer,
)
report = indexer.index_documents(
    [DocumentChunk(page_content="...", metadata={"source": "risk.md"})]
)
```

如果需要实体向量化图谱，把 `embedding_provider` 传给 `Neo4jGraphWriter`，并设置 `create_vector_index=True` 与 `vector_dimensions`。

## 图谱召回

```python
from rtrieval_engine.retrieval import (
    CommunityGraphRetriever,
    HybridGraphRetriever,
    LocalGraphRetriever,
    SemanticGraphRetriever,
)
from rtrieval_engine.storage import Neo4jGraphStorage


graph_storage = Neo4jGraphStorage(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
)

retriever = HybridGraphRetriever(
    local_retriever=LocalGraphRetriever(graph_storage),
    semantic_retriever=SemanticGraphRetriever(graph_storage, embedding),
    community_retriever=CommunityGraphRetriever(graph_storage),
)

relationships, communities = retriever.search_context("项目风险")
```

## 增量构建

`SourceCache` 只负责 hash diff，不负责扫描策略、删除策略或任务调度。宿主项目可以按自己的业务流程组合：

```python
from rtrieval_engine.indexing import SourceCache, build_file_state


cache = SourceCache.load(".cache/sources.json")
current = build_file_state(["docs/risk.md"], source_id="path")
diff = cache.diff(current)

for source in diff.to_remove:
    writer.remove_source(source)

# 宿主项目读取 diff.to_process 对应文档并调用 GraphIndexer

cache.replace(current)
cache.save(".cache/sources.json")
```

## 社区检测与总结

```python
from rtrieval_engine.indexing import CommunityDetector, CommunitySummarizer
from rtrieval_engine.storage import Neo4jCommunityStorage


community_storage = Neo4jCommunityStorage(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
)

CommunityDetector(storage=community_storage).run()
CommunitySummarizer(
    storage=community_storage,
    llm_provider=MyLLMProvider(),
    threshold=20,
).summarize_pending()
```

## 本地检查

```bash
python -m pytest
python -m compileall -q src tests
ruff check src tests
ruff format --check src tests
```

这个包不保留独立 `pre-commit`。检查规则由 monorepo 根目录统一维护。
