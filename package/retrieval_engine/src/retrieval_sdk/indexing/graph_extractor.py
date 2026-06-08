from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from retrieval_sdk.domain import GraphExtraction
from retrieval_sdk.parsers import parse_graph_extraction
from retrieval_sdk.prompts import DEFAULT_GRAPH_EXTRACTION_PROMPT, render_prompt
from retrieval_sdk.providers import LLMProvider

GraphExtractionParser = Callable[[str], GraphExtraction]
MessageBuilder = Callable[[str, dict[str, Any]], list[dict[str, str]]]


DEFAULT_GRAPH_USER_PROMPT = "请提取知识图谱：\n\n{{ text }}"


@dataclass(slots=True)
class GraphExtractor:
    """使用注入的 LLM 从文本中抽取图谱实体和关系。"""

    llm_provider: LLMProvider
    prompt_template: str = DEFAULT_GRAPH_EXTRACTION_PROMPT
    user_prompt_template: str = DEFAULT_GRAPH_USER_PROMPT
    parser: GraphExtractionParser = parse_graph_extraction
    llm_options: dict[str, Any] = field(default_factory=dict)
    message_builder: MessageBuilder | None = None

    def extract(self, text: str, **variables: Any) -> GraphExtraction:
        if not text.strip():
            return GraphExtraction(entities=[], relationships=[])

        render_variables = {"text": text, **variables}
        messages = self.build_messages(text, render_variables)
        raw_response = self.llm_provider.complete(messages, **self.llm_options)
        return self.parser(raw_response)

    def build_messages(
        self,
        text: str,
        variables: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        render_variables = {"text": text, **(variables or {})}
        if self.message_builder is not None:
            return self.message_builder(text, render_variables)

        system_prompt = render_prompt(self.prompt_template, **render_variables)
        user_prompt = render_prompt(self.user_prompt_template, **render_variables)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]


def extract_graph(
    text: str,
    *,
    llm_provider: LLMProvider,
    prompt_template: str = DEFAULT_GRAPH_EXTRACTION_PROMPT,
    user_prompt_template: str = DEFAULT_GRAPH_USER_PROMPT,
    parser: GraphExtractionParser = parse_graph_extraction,
    llm_options: dict[str, Any] | None = None,
    **variables: Any,
) -> GraphExtraction:
    """一次性图谱抽取便利函数。"""
    return GraphExtractor(
        llm_provider=llm_provider,
        prompt_template=prompt_template,
        user_prompt_template=user_prompt_template,
        parser=parser,
        llm_options=llm_options or {},
    ).extract(text, **variables)
