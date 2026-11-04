"""Cost, token, and execution tracking service for the Scientific Discovery Agent.

Calculates token counts, estimated Gemini API expenditure, and Docker execution metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any


# Standard pricing per million tokens for Google Gemini 3.8 / 3.5 Flash
INPUT_COST_PER_MILLION = 0.15   # $0.15 per 1M prompt tokens
OUTPUT_COST_PER_MILLION = 0.60  # $0.60 per 1M completion tokens


@dataclass
class ExecutionMetrics:
    """Stores execution metrics, token estimates, and costs for a discovery run."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    execution_time_seconds: float = 0.0
    docker_sandboxed: bool = True
    figures_analyzed: int = 0
    papers_retrieved: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
            "execution_time_seconds": round(self.execution_time_seconds, 3),
            "docker_sandboxed": self.docker_sandboxed,
            "figures_analyzed": self.figures_analyzed,
            "papers_retrieved": self.papers_retrieved,
            "timestamp": self.timestamp,
        }


def estimate_tokens(text: str) -> int:
    """Approximate token count for a text string (avg ~4 characters per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate estimated USD cost based on token consumption."""
    input_cost = (prompt_tokens / 1_000_000.0) * INPUT_COST_PER_MILLION
    output_cost = (completion_tokens / 1_000_000.0) * OUTPUT_COST_PER_MILLION
    return round(input_cost + output_cost, 6)


def track_discovery_metrics(
    research_result: dict[str, Any],
    execution_duration: float = 0.0,
) -> ExecutionMetrics:
    """Compute aggregate execution metrics from an orchestrator result dictionary."""
    lit_text = str(research_result.get("literature_review", ""))
    hyp_text = str(research_result.get("hypothesis", ""))
    crit_text = str(research_result.get("statistical_critic_result", {}))
    mem_text = str(research_result.get("memory_context", ""))
    topic_text = str(research_result.get("research_topic", ""))

    prompt_tokens = estimate_tokens(topic_text + mem_text + "system_instruction_context")
    completion_tokens = estimate_tokens(lit_text + hyp_text + crit_text)
    total_tokens = prompt_tokens + completion_tokens

    cost = calculate_cost(prompt_tokens, completion_tokens)

    experiment = research_result.get("experiment", {})
    metadata = experiment.get("metadata", {})
    docker_status = metadata.get("docker_sandboxed", True)
    exec_time = execution_duration or metadata.get("execution_time_seconds", 0.0)

    figures_count = research_result.get("multimodal_figures_count", 0)
    papers_count = len(research_result.get("retrieved_papers", [])) or research_result.get("paper_count", 1)

    return ExecutionMetrics(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=cost,
        execution_time_seconds=exec_time,
        docker_sandboxed=docker_status,
        figures_analyzed=figures_count,
        papers_retrieved=papers_count,
    )
