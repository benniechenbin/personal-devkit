# 变更日志

本文件记录 `personal-devkit` monorepo 层面的重要变更，包括 workspace 结构、统一工具链、CI 配置，以及新增或移除 package/template 的记录。

## Unreleased

- 增加 `templates/_shared/` 作为模板维护侧共享源头，并提供同步脚本；生成项目仍保持自包含，不新增运行时 common 包依赖。
- 增加根目录 `Makefile` 检查入口，CI 补充共享模板同步、`.env.example`、格式化和 Copier 模板闭环检查。
- 统一模板环境变量示例检查目标命名，并降低根 coverage 报告中的模板占位模块噪音。
- 将根级主类型检查和 pre-commit mypy 限定在当前稳定通过的模板与共享脚本范围，保留 `make type-retrieval` 作为 retrieval SDK 类型收敛入口。
- 将现有 README 文档统一为中文，并新增 `templates/README.md` 说明模板用途、差异和 `_shared` 同步流程。
- 增加 `packages/document_engine` 能力包和 `apps/ocr_app` 应用壳，完成 OCR 项目的最小分层迁移；应用负责配置、日志、CLI 和落盘，package 保持可复用文档解析能力。
- 将 `packages/document_engine` 从 `loguru` 解耦，改用标准库 logging，并增加防止 package 重新 import `loguru` 的边界测试。
- 将 `packages/document_engine` 的公式识别和视觉 OCR 重依赖拆为 `formula`、`vision` extras；`apps/ocr_app` 显式依赖 `document-engine[formula,vision]` 以保持完整运行能力。

## 0.1.0 - 2026-06-08

- 初始化 `personal-devkit` monorepo。
- 纳入首个 package：`packages/retrieval_engine`。
- 纳入两个项目模板：`templates/python_project_boilerplate` 与 `templates/agent_enterprise_boilerplate`。
- 增加根目录统一的 `uv` workspace、pytest、Ruff、MyPy、coverage、pre-commit 与 GitHub Actions CI 配置。
- 清理子项目迁移遗留的嵌套 Git 仓库、独立 CI 配置、本地虚拟环境、缓存、日志和覆盖率产物。
- 明确版本记录策略：根目录维护 monorepo 变更日志，package 维护各自 `CHANGELOG.md`，template 仅维护 `VERSION.md`。
