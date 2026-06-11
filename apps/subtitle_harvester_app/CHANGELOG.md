# 变更日志

本文件记录 `subtitle-harvester-app` 的重要变更。

格式参考 [变更日志维护规范](https://keepachangelog.com/en/1.1.0/)，当前作为应用内项目按语义化版本维护。

## [0.1.0] - 2026-06-11

### 新增

- 初始化 TMDb 字幕候选采集 CLI。
- 增加规范化媒体候选条目的 JSON 输出器。
- 增加应用级 settings、日志启动、Docker 配置、Make 目标、测试和 `.env.example` 生成。
- 增加项目文档和生成产物忽略规则。

### 修复

- 将模板遗留的控制台脚本名替换为 `subtitle-harvester-app`。
- 入口测试改为离线运行，不再依赖真实 TMDb 请求。
