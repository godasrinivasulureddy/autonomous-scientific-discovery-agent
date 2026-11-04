"""Unit tests for cost and token tracking service (Week 4, Member 1)."""

import pytest
from services.cost_tracker import (
    estimate_tokens,
    calculate_cost,
    track_discovery_metrics,
    ExecutionMetrics,
)


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello world") >= 1
    long_text = "a" * 400
    assert estimate_tokens(long_text) == 100


def test_calculate_cost():
    cost = calculate_cost(prompt_tokens=1_000_000, completion_tokens=1_000_000)
    assert cost == pytest.approx(0.75, abs=1e-4)

    zero_cost = calculate_cost(0, 0)
    assert zero_cost == 0.0


def test_track_discovery_metrics():
    mock_result = {
        "research_topic": "CRISPR Editing",
        "literature_review": "Literature findings on Cas9 specificity.",
        "hypothesis": "Cas9 variant reduces off-targets.",
        "experiment": {
            "status": "success",
            "metadata": {"execution_time_seconds": 0.55, "docker_sandboxed": True},
        },
        "statistical_critic_result": {"status": "evaluated", "significant": True},
        "multimodal_figures_count": 2,
    }

    metrics = track_discovery_metrics(mock_result, execution_duration=1.2)

    assert isinstance(metrics, ExecutionMetrics)
    assert metrics.total_tokens > 0
    assert metrics.estimated_cost_usd >= 0.0
    assert metrics.execution_time_seconds == 1.2
    assert metrics.docker_sandboxed is True
    assert metrics.figures_analyzed == 2

    metrics_dict = metrics.to_dict()
    assert "estimated_cost_usd" in metrics_dict
    assert "docker_sandboxed" in metrics_dict
