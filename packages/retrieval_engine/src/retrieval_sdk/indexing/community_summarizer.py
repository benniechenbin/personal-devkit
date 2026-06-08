from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from retrieval_sdk.domain import (
    BuildReport,
    CommunityCandidate,
    CommunitySummary,
)
from retrieval_sdk.parsers import parse_community_summary
from retrieval_sdk.prompts import DEFAULT_COMMUNITY_SUMMARY_PROMPT, render_prompt
from retrieval_sdk.providers import LLMProvider
from retrieval_sdk.storage.community import CommunityStorage

CommunitySummaryParser = Callable[[str], CommunitySummary]


@dataclass(slots=True)
class CommunitySummarizer:
    """使用注入的 LLM 和存储适配器总结图谱聚落。"""

    storage: CommunityStorage
    llm_provider: LLMProvider
    prompt_template: str = DEFAULT_COMMUNITY_SUMMARY_PROMPT
    parser: CommunitySummaryParser = parse_community_summary
    llm_options: dict[str, Any] = field(default_factory=dict)
    threshold: int = 20
    top_node_limit: int = 30
    limit: int | None = None
    strict: bool = False

    def summarize_candidate(self, candidate: CommunityCandidate) -> CommunitySummary:
        words = ", ".join(candidate.top_nodes)
        prompt = render_prompt(
            self.prompt_template,
            words=words,
            community_id=candidate.community_id,
            size=candidate.size,
            top_nodes=candidate.top_nodes,
        )
        raw_response = self.llm_provider.complete(
            [{"role": "user", "content": prompt}],
            **self.llm_options,
        )
        return self.parser(raw_response)

    def summarize_pending(self) -> BuildReport:
        candidates = self.storage.list_unsummarized_communities(
            threshold=self.threshold,
            top_node_limit=self.top_node_limit,
            limit=self.limit,
        )
        report = BuildReport(
            total_documents=len(candidates),
            total_chunks=len(candidates),
        )

        for candidate in candidates:
            try:
                summary = self.summarize_candidate(candidate)
                self.storage.save_community_summary(
                    community_id=candidate.community_id,
                    size=candidate.size,
                    summary=summary,
                )
                report.updated += 1
            except Exception as exc:
                if self.strict:
                    raise
                report.errors.append(f"{candidate.community_id}: {exc}")

        return report
