# 更新日志

所有对 `crawl-engine` 项目的重要变更都将记录在此文件中。

## [0.2.1] - 2026-06-11

### 新增

- 增加 `crawl_engine.engines` 子包导出，统一导出 `HttpxEngine` 和 `Crawl4AIEngine`。
- 补齐顶层 `crawl_engine` 的下载、解压相关 schema 导出。
- 增加 `ArchiveExtractor` 单元测试，覆盖正常解压、路径穿越、非 zip、删除原压缩包和限制项。
- `AttachmentDownloader` 改为流式下载写入，避免将附件内容一次性读入内存。
- 增加 `AttachmentRequest.max_size_bytes`，支持限制单个附件下载体积。

### 变更

- `ArchiveExtractor` 会先校验 zip 内所有目标路径，再开始写入文件，避免路径异常时留下部分解压产物。
- `AttachmentDownloader` 会先写入临时 `.part` 文件，下载成功后再替换为最终文件。
- `AttachmentDownloader` 会优先使用 `Content-Length` 判断大小；没有该响应头时，会在流式写入过程中累计校验。

## [0.2.0] - 2026-06-11

### 新增

- 增加 `downloads.ArchiveExtractor`，用于下载后压缩包解压。
- 增加 `ArchiveRequest`、`ExtractedFile`、`ExtractedArchive` schema。
- `ArchiveExtractor` 当前支持 zip 文件解压、安全路径校验、文件数量限制、解压体积限制、自动重命名和可选删除原压缩包。
- 从 `crawl_engine.downloads` 和顶层 `crawl_engine` 导出 `ArchiveExtractor`。

### 说明

- `ArchiveExtractor` 只处理通用压缩包解压，不包含字幕、图片、文档等业务筛选规则。

## [0.1.0] - 2026-06-09

### 新增
- **初始版本发布**。
- **HttpxEngine**: 实现了基于 `httpx` 的轻量级异步爬取引擎，支持自动重试机制。
- **Crawl4AIEngine**: 实现了基于 `crawl4ai` 的高级爬取引擎，支持 JS 渲染、噪声去除和结构化数据提取。
- **统一数据模型**: 定义了 `ScrapeRequest`, `Crawl4AIRequest` 和 `ScrapeResponse` 模型，确保引擎接口的一致性。
- **可选依赖**: 支持通过 `crawl-engine[crawl4ai]` 安装高级引擎所需的依赖。
- **基础测试**: 增加了对引擎功能和 schema 的单元测试。
