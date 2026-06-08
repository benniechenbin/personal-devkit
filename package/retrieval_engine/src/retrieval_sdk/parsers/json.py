from __future__ import annotations

import json
import re
from typing import Any

from retrieval_sdk.domain import (
    CommunitySummary,
    GraphEntity,
    GraphExtraction,
    GraphRelation,
)


def extract_json_payload(text: str) -> str:
    """从 LLM 响应中提取最可能的 JSON 载荷。"""
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()

    object_payload = extract_json_object(stripped)
    if object_payload:
        return object_payload
    return stripped


def extract_json_object(text: str) -> str:
    """从文本中提取第一个括号平衡的顶层 JSON 对象。"""
    start = text.find("{")
    if start < 0:
        return ""

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    return ""


def parse_json_payload(text: str) -> Any:
    """解析原始文本或 fenced 代码块中的 JSON。"""
    payload = extract_json_payload(text)
    return json.loads(payload)


def parse_graph_extraction(text: str) -> GraphExtraction:
    payload = parse_json_payload(text)
    if not isinstance(payload, dict):
        raise ValueError("graph extraction payload must be a JSON object.")

    entities = [
        GraphEntity(
            id=str(item.get("id", "")).strip(),
            type=str(item.get("type", "")).strip(),
            summary=str(item.get("summary", "")).strip(),
            metadata=_coerce_metadata(item.get("metadata")),
        )
        for item in _iter_dicts(payload.get("entities", []))
    ]
    relationships = [
        GraphRelation(
            source=str(item.get("source", "")).strip(),
            target=str(item.get("target", "")).strip(),
            relation=str(item.get("relation", "")).strip(),
            source_summary=str(item.get("source_summary", "")).strip(),
            target_summary=str(item.get("target_summary", "")).strip(),
            metadata=_coerce_metadata(item.get("metadata")),
        )
        for item in _iter_dicts(payload.get("relationships", []))
    ]

    return GraphExtraction(
        entities=[entity for entity in entities if entity.id],
        relationships=[
            relation
            for relation in relationships
            if relation.source and relation.target and relation.relation
        ],
    )


def parse_community_summary(text: str) -> CommunitySummary:
    payload = parse_json_payload(text)
    if not isinstance(payload, dict):
        raise ValueError("community summary payload must be a JSON object.")

    confidence = payload.get("confidence")
    return CommunitySummary(
        name=str(payload.get("name", "")).strip(),
        summary=str(payload.get("summary", "")).strip(),
        cluster_type=str(payload.get("cluster_type", "")).strip(),
        confidence=float(confidence) if confidence is not None else None,
    )


def _iter_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]

def _coerce_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return dict(value)