# 个人财务应用

个人财务分析与管理工具 (v0.2.0)。

## 特性 (v0.2.0)
- **Excel/CSV 账单导入**: 自动读取 `个人预算.xlsx` 中的 `交易` 页签。
- **数据标准化**: 自动适配、清理并映射中文字段（支持“日期”、“总额”、“类别”等）。
- **财务指标分析**: 汇总总流入、总流出、净流量，并按分类聚合开销。
- **AI 理财建议**: 结合 OpenAI 接口，自动根据当月账单生成 3 条具体优化建议。
- **历史记录持久化**: 将分析结果与标准化后的交易明细存入 SQLite (`data/finance.db`)。
- **Markdown 月报归档**: 自动生成月度分析报告 (`data/reports/YYYY-MM-finance-report.md`)，作为后续分析的上下文语料。

## 快速开始

### 前置依赖
确保安装了 [uv](https://github.com/astral-sh/uv)。

### 运行配置
复制环境变量模板并填入你的 OpenAI API Key:
```bash
cp .env.example .env
```

## 重要说明

本工具中的 AI 理财建议仅用于个人月度复盘和消费习惯分析，不构成专业财务、投资、税务或法律建议。

系统中的金额汇总、分类统计、净流量等数据由 Python 程序确定性计算；LLM 只基于这些事实生成自然语言解释和建议。

### 运行分析
使用真实账本数据执行分析：
```bash
uv run personal-finance-app /path/to/你的个人预算.xlsx
# 或者使用旧名
uv run base-app /path/to/你的个人预算.xlsx
```

## 数据结构
- **data/finance.db**: 存储分析快照、分类汇总及交易流水。
- **data/reports/**: 存储 Markdown 格式的财务报告。
- **logs/**: 存储应用运行日志。
