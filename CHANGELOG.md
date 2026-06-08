# 变更日志

本文件记录 `personal-devkit` monorepo 层面的重要变更，包括 workspace 结构、统一工具链、CI 配置，以及新增或移除 package/template 的记录。

## Unreleased

- 增加 `templates/_shared/` 作为模板维护侧共享源头，并提供同步脚本；生成项目仍保持自包含，不新增运行时 common 包依赖。

## 0.1.0 - 2026-06-08

- 初始化 `personal-devkit` monorepo。
- 纳入首个 package：`package/retrieval_engine`。
- 纳入两个项目模板：`templates/python_project_boilerplate` 与 `templates/agent_enterprise_boilerplate`。
- 增加根目录统一的 `uv` workspace、pytest、Ruff、MyPy、coverage、pre-commit 与 GitHub Actions CI 配置。
- 清理子项目迁移遗留的嵌套 Git 仓库、独立 CI 配置、本地虚拟环境、缓存、日志和覆盖率产物。
- 明确版本记录策略：根目录维护 monorepo 变更日志，package 维护各自 `CHANGELOG.md`，template 仅维护 `VERSION.md`。
