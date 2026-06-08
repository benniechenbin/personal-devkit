from __future__ import annotations

from retrieval_engine.prompts.renderer import (
    _render_with_lightweight_replacement,
    render_prompt,
)


def test_render_prompt_replaces_scalar_variable() -> None:
    result = render_prompt(
        "主题：{{ topic }}",
        topic="GraphRAG",
    )

    assert result == "主题：GraphRAG"


def test_lightweight_renderer_joins_list_values() -> None:
    result = _render_with_lightweight_replacement(
        "关键词：{{ words }}",
        {"words": ["GraphRAG", "Qdrant", "Neo4j"]},
    )

    assert result == "关键词：GraphRAG, Qdrant, Neo4j"


def test_lightweight_renderer_keeps_unknown_variables() -> None:
    result = _render_with_lightweight_replacement(
        "主题：{{ topic }}，缺失：{{ missing }}",
        {"topic": "GraphRAG"},
    )

    assert result == "主题：GraphRAG，缺失：{{ missing }}"
