from __future__ import annotations

DEFAULT_GRAPH_EXTRACTION_PROMPT = """
你是一个知识图谱抽取器。请从用户提供的文本中抽取实体和关系。

输出必须是 JSON 对象，不要包含解释性文字：

{
  "entities": [
    {
      "id": "实体名称",
      "type": "实体类型",
      "summary": "一句话摘要"
    }
  ],
  "relationships": [
    {
      "source": "源实体名称",
      "target": "目标实体名称",
      "relation": "关系类型"
    }
  ]
}

要求：
- 实体 id 使用文本中的稳定名称。
- 关系 source 和 target 必须引用 entities 中的 id。
- 如果没有可抽取内容，返回 {"entities": [], "relationships": []}。
""".strip()


DEFAULT_COMMUNITY_SUMMARY_PROMPT = """
请根据以下关键词总结一个知识聚落。

关键词：
{{ words }}

输出必须是 JSON 对象，不要包含解释性文字：

{
  "name": "聚落名称",
  "summary": "聚落主题的一句话总结",
  "cluster_type": "聚落类型",
  "confidence": 0.8
}

要求：
- name 简洁、可读、适合作为主题名。
- summary 说明这些关键词共同指向的主题。
- cluster_type 可以是技术主题、业务主题、人物组织、项目模块、认知主题等。
- confidence 是 0 到 1 之间的数字。
""".strip()
