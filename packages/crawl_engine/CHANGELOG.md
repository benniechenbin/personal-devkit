# 更新日志

所有对 `crawl-engine` 项目的重要变更都将记录在此文件中。

## [0.1.0] - 2026-06-09

### 新增
- **初始版本发布**。
- **HttpxEngine**: 实现了基于 `httpx` 的轻量级异步爬取引擎，支持自动重试机制。
- **Crawl4AIEngine**: 实现了基于 `crawl4ai` 的高级爬取引擎，支持 JS 渲染、噪声去除和结构化数据提取。
- **统一数据模型**: 定义了 `ScrapeRequest`, `Crawl4AIRequest` 和 `ScrapeResponse` 模型，确保引擎接口的一致性。
- **可选依赖**: 支持通过 `crawl-engine[crawl4ai]` 安装高级引擎所需的依赖。
- **基础测试**: 增加了对引擎功能和 schema 的单元测试。
## [0.2.0] - 2026-06-11

### 新增

- 增加 `downloads.ArchiveExtractor`，用于下载后压缩包解压。
- 增加 `ArchiveRequest`、`ExtractedFile`、`ExtractedArchive` schema。
- `ArchiveExtractor` 当前支持 zip 文件解压、安全路径校验、文件数量限制、解压体积限制、自动重命名和可选删除原压缩包。
- 从 `crawl_engine.downloads` 和顶层 `crawl_engine` 导出 `ArchiveExtractor`。

### 说明

- `ArchiveExtractor` 只处理通用压缩包解压，不包含字幕、图片、文档等业务筛选规则。
