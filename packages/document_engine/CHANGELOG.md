# 更新日志

所有对 `document-engine` 项目的重要变更都将记录在此文件中。

## [0.2.0] - 2026-06-09

### 新增
- **表格文档解析支持**: 新增 `TabularReader`，支持解析 `.xlsx`, `.xlsm`, `.csv` 格式。
- **Word 文档解析支持**: 新增 `DocxReader`，支持解析 `.docx` 格式。
- **智能文档路由**: 新增 `DocumentRouter`，可自动分发解析任务。
- **目录结构重构**:
  - 引入 `readers/` 用于存放格式解析器。
  - `engines/` 专注于复杂解析策略（如矢量 PDF）。
  - `TabularEngine` / `DocxEngine` 保留为兼容入口，推荐迁移至 `TabularReader` / `DocxReader`。
- **依赖更新**: 新增 `openpyxl`, `tabulate`, `python-docx` 为基础依赖。


### 优化
- 改进引擎架构设计，为后续非 PDF 格式留出扩展空间。
- `VectorPipeline` 的 `process_pdf` 现在单纯返回 `Fragment` 列表，职责更加纯粹。

## [0.1.0] - 2026-06-09

### 新增
- **初始版本发布**。
- **文档解析引擎**: 实现了基于 PyMuPDF 的基础解析能力。
- **可选依赖支持**:
  - `formula`: 支持数学公式提取（集成 pix2text）。
  - `vision`: 支持基于 PaddleOCR 的视觉解析。
- **构建系统**: 适配 Hatchling 构建系统，支持生成 Wheel 包。
