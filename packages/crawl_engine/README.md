# 爬取引擎（私有 SDK）

`crawl-engine` 是 `personal-devkit` 个人开发工具集中的一个网页爬取核心组件。它旨在为单体仓库（Monorepo）中的其他应用和包提供统一、鲁棒的网页抓取接口。

## 定位

本项目作为个人私有 SDK 维护，主要解决：
- **统一接口**：为不同抓取引擎提供标准化的 `ScrapeRequest` 和 `ScrapeResponse`。
- **能力分层**：
  - `HttpxEngine`：轻量级、高并发，适用于静态页面快速抓取。
  - `Crawl4AIEngine`：重型引擎，支持浏览器渲染和智能噪声去除。
- **私有集成**：专为本仓库内的 OCR 或 RAG 流程提供输入管道。

## 开发与集成

由于本项目不发布至公共 PyPI，推荐使用 `uv` 在 monorepo 环境下进行本地开发集成。

### 在本仓库其他项目中使用

在目标项目的 `pyproject.toml` 中通过 workspace 引用：

```toml
[tool.uv.sources]
crawl-engine = { workspace = true }
```

### 环境准备

如果需要使用高级抓取功能（Crawl4AI），需确保安装了对应的额外依赖：

```bash
# 在项目根目录执行同步
uv sync --all-packages --extra crawl4ai
```

## 快速上手

### 1. 轻量级静态抓取 (HttpxEngine)

```python
import asyncio
from crawl_engine.engines.httpx_engine import HttpxEngine
from crawl_engine.schema import ScrapeRequest

async def main():
    engine = HttpxEngine()
    request = ScrapeRequest(url="https://example.com")
    response = await engine.fetch_content(request)

    if response.success:
        print(f"抓取成功: {response.url}")

    await engine.close()

asyncio.run(main())
```

### 2. 深度抓取与噪声去除 (Crawl4AIEngine)

```python
import asyncio
from crawl_engine.engines.crawl4ai_engine import Crawl4AIEngine
from crawl_engine.schema import Crawl4AIRequest

async def main():
    # 需安装 crawl4ai 依赖
    engine = Crawl4AIEngine(headless=True)
    request = Crawl4AIRequest(
        url="https://github.com/trending",
        remove_noise=True
    )
    response = await engine.fetch_content(request)

    if response.success:
        print(f"Markdown 内容提取成功: {len(response.content)} chars")

asyncio.run(main())
```
### 3. 附件下载与压缩包解压

`AttachmentDownloader` 使用流式下载写入文件，避免把附件一次性读入内存；下载内容会先写入临时 `.part` 文件，成功后再替换为最终文件。可以通过 `AttachmentRequest.max_size_bytes` 限制单个附件大小。

```python
import asyncio
from pathlib import Path

from core_utils.files import ArchiveExtractor, ArchiveRequest
from crawl_engine.downloads import AttachmentDownloader
from crawl_engine.schema import AttachmentRequest

async def main():
    downloader = AttachmentDownloader()
    extractor = ArchiveExtractor()

    try:
        downloaded = await downloader.download(
            AttachmentRequest(
                url="https://example.com/archive.zip",
                max_size_bytes=100 * 1024 * 1024,
            ),
            output_dir="downloads",
        )

        if downloaded.success and downloaded.path:
            extracted = await extractor.extract_async(
                ArchiveRequest(
                    archive_path=downloaded.path,
                    output_dir=Path("extracted"),
                )
            )
            print(extracted.files)
    finally:
        await downloader.close()

asyncio.run(main())
```

---

### 4. 压缩包解压行为

`ArchiveExtractor` 当前只处理通用 zip 解压，不包含字幕、图片、文档等业务筛选规则。它会在写入文件前检查压缩包条目路径，避免 `../` 或绝对路径把文件解压到目标目录外。

当前支持：

```text
正常 zip 解压
嵌套目录解压
已有文件自动重命名
路径穿越被拒绝
非 zip 返回失败
delete_archive=True 成功删除原压缩包
max_files 限制
max_total_uncompressed_bytes 限制
异步包装 extract_async
```

## 核心设计

- **架构**：遵循插件化设计，引擎可插拔。
- **异常**：内置 `tenacity` 重试与全局异常捕获，确保流水线不因单点抓取失败而崩溃。
- **Schema**：强制 Pydantic 类型校验，提供 `extracted_data` 字段支持结构化输出。

## 维护记录

详见 [CHANGELOG.md](./CHANGELOG.md)。
