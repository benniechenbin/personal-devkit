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
