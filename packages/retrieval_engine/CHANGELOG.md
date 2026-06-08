# 变更日志

本文件记录 `retrieval-sdk` 包的变更。

## 0.1.0 - 2026-06-08

- 初始化 `retrieval-sdk` 包。
- 提供向量检索、词法检索、混合检索、图检索与社区检索相关模块。
- 提供 Markdown/JSON 解析、prompt 渲染、索引构建、图存储与可选 Qdrant/Neo4j 集成。
- 迁入 `personal-devkit` monorepo，并改由根目录统一管理 lint、test、type-check、coverage、pre-commit 与 CI。
- 增加 monorepo 级 integration smoke tests，验证 `document_engine -> retrieval_engine` 跨 package 链路，以及 retrieval in-memory 全链路。
