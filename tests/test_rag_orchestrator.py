
from unittest.mock import patch

import pytest

from agents.rag_orchestrator import run_rag_research


def test_rag_research_integration():
    """Verify retrieved papers reach the existing agent workflow."""

    sample_papers = [
        {
            "title": "Diabetes Prediction Using ML",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/example",
            "text": "Machine learning can support diabetes prediction.",
        }
    ]

    def mock_search(query, top_k=3):
        assert query == "Diabetes prediction"
        assert top_k == 3
        return sample_papers

    with patch(
        "agents.rag_orchestrator.run_research_workflow",
        return_value={
            "research_topic": "Diabetes prediction",
            "literature_review": "Research summary",
            "hypothesis": "Testable hypothesis",
            "experiment": {"status": "not_executed"},
        },
    ) as mock_workflow:

        result = run_rag_research(
            research_topic="Diabetes prediction",
            search_papers=mock_search,
        )

    assert result["retrieval_count"] == 1
    assert result["retrieved_papers"] == sample_papers

    context = mock_workflow.call_args.kwargs["paper_text"]

    assert "Diabetes Prediction Using ML" in context
    assert "Machine learning can support diabetes prediction." in context
    assert "https://arxiv.org/abs/example" in context


def test_rag_rejects_empty_topic():
    with pytest.raises(ValueError, match="Research topic"):
        run_rag_research("", search_papers=lambda *args, **kwargs: [])


def test_rag_rejects_invalid_top_k():
    with pytest.raises(ValueError, match="top_k"):
        run_rag_research(
            "Diabetes prediction",
            search_papers=lambda *args, **kwargs: [],
            top_k=0,
        )


def test_rag_rejects_empty_retrieval():
    with pytest.raises(ValueError, match="No relevant research papers"):
        run_rag_research(
            "Diabetes prediction",
            search_papers=lambda *args, **kwargs: [],
        )
