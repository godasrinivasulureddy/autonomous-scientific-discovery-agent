from unittest.mock import patch

import pytest

from agents.rag_orchestrator import run_rag_research


def sample_paper():
    return {
        "paper_id": "arxiv:example",
        "title": "Diabetes Prediction Using ML",
        "source": "arxiv",
        "url": "https://arxiv.org/abs/example",
        "text": "Machine learning can support diabetes prediction.",
        "score": 0.92,
    }


def mock_workflow_result():
    return {
        "research_topic": "Diabetes prediction",
        "literature_review": "Research summary",
        "hypothesis": "Testable hypothesis",
        "experiment": {"status": "not_executed"},
    }


def test_rag_research_integration():
    """Verify evidence and citation metadata reach the workflow."""
    papers = [sample_paper()]

    def mock_search(query, top_k=3):
        assert query == "Diabetes prediction"
        assert top_k == 3
        return papers

    with patch(
        "agents.rag_orchestrator.run_research_workflow",
        return_value=mock_workflow_result(),
    ) as mock_workflow:
        result = run_rag_research(
            research_topic="Diabetes prediction",
            search_papers=mock_search,
        )

    assert result["retrieval_count"] == 1
    assert result["retrieved_papers"] == papers
    assert result["citation_metadata"] == [
        {
            "evidence_id": 1,
            "title": "Diabetes Prediction Using ML",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/example",
        }
    ]

    context = mock_workflow.call_args.kwargs["paper_text"]
    assert "Evidence [1]" in context
    assert "Diabetes Prediction Using ML" in context
    assert "Machine learning can support diabetes prediction." in context
    assert "https://arxiv.org/abs/example" in context


def test_rag_rejects_empty_topic():
    with pytest.raises(ValueError, match="Research topic"):
        run_rag_research(
            "",
            search_papers=lambda *args, **kwargs: [],
        )


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True, "3", None])
def test_rag_rejects_invalid_top_k(top_k):
    with pytest.raises(ValueError, match="top_k"):
        run_rag_research(
            "Diabetes prediction",
            search_papers=lambda *args, **kwargs: [],
            top_k=top_k,
        )


def test_rag_rejects_non_callable_search():
    with pytest.raises(ValueError, match="callable"):
        run_rag_research(
            "Diabetes prediction",
            search_papers=None,
        )


def test_rag_rejects_empty_retrieval():
    with pytest.raises(ValueError, match="No relevant research papers"):
        run_rag_research(
            "Diabetes prediction",
            search_papers=lambda *args, **kwargs: [],
        )


def test_rag_rejects_papers_without_usable_text():
    papers = [
        {
            "title": "Missing text",
            "source": "arxiv",
            "url": "https://example.org/paper",
            "text": " ",
        }
    ]

    with pytest.raises(ValueError, match="no usable text"):
        run_rag_research(
            "Diabetes prediction",
            search_papers=lambda *args, **kwargs: papers,
        )


def test_rag_preserves_multiple_papers_and_citations():
    papers = [
        sample_paper(),
        {
            "paper_id": "pubmed:example",
            "title": "Second Study",
            "source": "pubmed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/example",
            "text": "A second study reports related evidence.",
            "score": 0.87,
        },
    ]

    with patch(
        "agents.rag_orchestrator.run_research_workflow",
        return_value=mock_workflow_result(),
    ) as mock_workflow:
        result = run_rag_research(
            research_topic="Diabetes prediction",
            search_papers=lambda *args, **kwargs: papers,
            top_k=2,
        )

    assert result["retrieval_count"] == 2
    assert len(result["citation_metadata"]) == 2
    assert result["citation_metadata"][0]["evidence_id"] == 1
    assert result["citation_metadata"][1]["evidence_id"] == 2

    context = mock_workflow.call_args.kwargs["paper_text"]
    assert "Evidence [1]" in context
    assert "Evidence [2]" in context
    assert "Second Study" in context
    assert "https://pubmed.ncbi.nlm.nih.gov/example" in context


def test_rag_skips_blank_paper_and_keeps_evidence_ids_sequential():
    papers = [
        {
            "title": "Blank Paper",
            "source": "arxiv",
            "url": "https://example.org/blank",
            "text": " ",
        },
        sample_paper(),
    ]

    with patch(
        "agents.rag_orchestrator.run_research_workflow",
        return_value=mock_workflow_result(),
    ) as mock_workflow:
        result = run_rag_research(
            research_topic="Diabetes prediction",
            search_papers=lambda *args, **kwargs: papers,
        )

    assert result["retrieval_count"] == 1
    assert result["citation_metadata"][0]["evidence_id"] == 1
    assert "Evidence [1]" in mock_workflow.call_args.kwargs["paper_text"]




@pytest.mark.parametrize(
    "topic,paper_title,paper_text",
    [
        (
            "Diabetes prediction",
            "Diabetes Prediction Study",
            "Evidence about diabetes prediction.",
        ),
        (
            "Protein structure prediction",
            "Protein Structure Study",
            "Evidence about protein structures.",
        ),
        (
            "Climate change forecasting",
            "Climate Forecasting Study",
            "Evidence about climate forecasting.",
        ),
    ],
)
def test_rag_retrieval_supports_multiple_topics(
    topic,
    paper_title,
    paper_text,
):
    papers = [
        {
            "paper_id": f"test:{topic}",
            "title": paper_title,
            "source": "test-journal",
            "url": "https://example.org/study",
            "text": paper_text,
        }
    ]

    def mock_search(query, top_k=3):
        assert query == topic
        return papers

    with patch(
        "agents.rag_orchestrator.run_research_workflow",
        return_value=mock_workflow_result(),
    ) as mock_workflow:
        result = run_rag_research(
            research_topic=topic,
            search_papers=mock_search,
        )

    assert result["retrieval_count"] == 1
    assert result["citation_metadata"][0]["title"] == paper_title

    context = mock_workflow.call_args.kwargs["paper_text"]
    assert topic in mock_workflow.call_args.kwargs["research_topic"]
    assert paper_title in context
    assert paper_text in context

