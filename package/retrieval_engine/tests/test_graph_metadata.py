from __future__ import annotations

from retrieval_sdk.domain import GraphEntity, GraphRelation
from retrieval_sdk.parsers import parse_graph_extraction


def test_graph_entity_and_relation_support_metadata() -> None:
    entity = GraphEntity(
        id="1#楼",
        type="building",
        metadata={
            "source_file": "sunlight_report.pdf",
            "page": 17,
        },
    )
    relation = GraphRelation(
        source="1#楼",
        target="302户",
        relation="包含",
        metadata={
            "evidence_text": "1#楼包含302户",
            "confidence": 0.9,
        },
    )

    assert entity.metadata["page"] == 17
    assert relation.metadata["confidence"] == 0.9


def test_parse_graph_extraction_preserves_metadata() -> None:
    raw = """
    {
      "entities": [
        {
          "id": "1#楼",
          "type": "building",
          "summary": "项目建筑",
          "metadata": {
            "source_file": "sunlight_report.pdf",
            "page": 17
          }
        }
      ],
      "relationships": [
        {
          "source": "1#楼",
          "target": "302户",
          "relation": "包含",
          "source_summary": "项目建筑",
          "target_summary": "住宅户",
          "metadata": {
            "evidence_text": "1#楼包含302户",
            "confidence": 0.9
          }
        }
      ]
    }
    """

    extraction = parse_graph_extraction(raw)

    assert extraction.entities[0].metadata["source_file"] == "sunlight_report.pdf"
    assert extraction.entities[0].metadata["page"] == 17
    assert extraction.relationships[0].source_summary == "项目建筑"
    assert extraction.relationships[0].target_summary == "住宅户"
    assert extraction.relationships[0].metadata["confidence"] == 0.9