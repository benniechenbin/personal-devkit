# personal-devkit

这是一个由 `uv` 管理的 Python monorepo，用来沉淀可复用 SDK 包、可执行个人应用，以及后续项目脚手架。

## 目录结构

- `packages/`：可复用库，应该提供相对稳定的公开 API。
- `apps/`：可执行应用，负责组合 packages，并持有应用自己的配置、CLI、存储和外部服务接线。
- `templates/`：用于生成新项目或 agent 服务的模板工程。
- `tests/`：跨包集成测试和共享测试替身。

## Packages

- `document_engine`：文档解析、Reader、PDF pipeline 和 Markdown 组装。
- `retrieval_engine`：向量检索、关键词检索、图谱检索和社区检索相关 SDK 原语。
- `crawl_engine`：HTTP/Crawl4AI 抓取、附件下载、压缩包提取和 Markdown 输出工具。
- `analysis_engine`：确定性数据归一化、指标计算、异常检测和报告构建。

packages 不应依赖 `apps/*`。重依赖或可选后端应通过惰性导入、可选 extras 或显式适配层隔离。

## Apps

- `ocr_app`：通过 `document_engine` 将 PDF 转换为 Markdown 的 CLI 应用。
- `personal_finance_app`：导入财务流水，生成确定性分析，并可选调用 LLM 生成建议的 CLI 应用。
- `subtitle_harvester_app`：字幕工作流应用，目前处于初步构建阶段；已纳入根 workspace/testpaths/pythonpath，后续会组合 `crawl_engine` 完成字幕爬取能力。

apps 可以通过 workspace 依赖使用 packages。应用专属配置、状态、存储、CLI 行为和外部服务编排应留在 app 内部。

## Templates

- `templates/python_project_boilerplate`：轻量 Python 应用模板。
- `templates/agent_enterprise_boilerplate`：带 workflow/runtime 结构的 agent 服务模板。

模板源码和生成模板文件会参与根测试与类型检查，但模板治理应和运行时代码治理分开推进。

## 开发命令

安装所有 workspace 包和开发工具：

```powershell
uv sync --all-packages --all-extras --group dev
```

常用检查：

```powershell
uv run ruff check .
uv run ruff format . --check
uv run pytest
```

聚合检查：

```powershell
make check
```

类型检查按边界拆分：

```powershell
make type
make type-retrieval
```

## Monorepo 规则

- 每个需要维护的 app/package 都要加入 `[tool.uv.workspace].members`。
- 每个需要维护的测试目录都要加入根 `tool.pytest.ini_options.testpaths`。
- 根 `pythonpath` 要和 workspace 成员保持一致，保证本地测试导入路径稳定。
- packages 不能反向 import apps，公共能力应沉淀到 packages。
- apps 可以依赖 packages，但应用配置、CLI、状态和产品编排不要下沉到 packages。
- 网络客户端默认必须安全；关闭 TLS 校验或自定义证书必须是调用方显式选择。
- OCR、浏览器、向量库、图库、文档解析等重依赖要优先使用惰性导入。
- CI、pre-commit、Makefile 的检查范围要保持一致，避免本地通过但 PR 漏检。
