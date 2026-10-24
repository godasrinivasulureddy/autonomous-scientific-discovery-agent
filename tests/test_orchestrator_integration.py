from unittest.mock import patch

import pytest

from agents.orchestrator import (
    run_research_from_papers,
    run_research_workflow,
)
from services.paper_fetcher import Paper


def make_paper(paper_id="arxiv:1234"):
    return Paper(
        paper_id=paper_id,
        title="Machine Learning Research",
        abstract="This paper studies machine learning methods.",
        authors=["Test Author"],
        url=f"https://arxiv.org/abs/{paper_id.split(':')[-1]}",
        published="2026-10-10",
        source="arxiv",
    )


def make_processed_record(paper=None, full_text="Extracted scientific PDF content."):
    paper = paper or make_paper()
    return {
        "title": paper.title,
        "source": paper.source,
        "url": paper.url,
        "full_text": full_text,
    }


def mock_research_result():
    return {
        "literature_review": "Sample literature review",
        "hypothesis": "Sample hypothesis",
        "experiment": {
            "status": "not_executed",
            "reason": "An approved experiment and dataset are required.",
        },
    }


def test_research_workflow_integration():
    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="Research gap: Limited evaluation data.",
        ) as mock_review,
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Hypothesis: More data improves accuracy.",
        ) as mock_hypothesis,
    ):
        result = run_research_workflow(
            research_topic="Diabetes Prediction",
            paper_text="Machine learning research paper.",
        )

    assert result["research_topic"] == "Diabetes Prediction"
    assert result["literature_review"] == (
        "Research gap: Limited evaluation data."
    )
    assert result["hypothesis"] == (
        "Hypothesis: More data improves accuracy."
    )
    assert result["experiment"]["status"] == "not_executed"

    mock_review.assert_called_once()
    mock_hypothesis.assert_called_once()


def test_paper_search_agent_integration():
    paper = make_paper()

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper],
        ),
        patch(
            "services.pdf_processor.process_paper",
            return_value=make_processed_record(paper),
        ) as mock_processor,
        patch(
            "agents.orchestrator.run_research_workflow",
            return_value=mock_research_result(),
        ) as mock_workflow,
    ):
        result = run_research_from_papers(
            research_topic="Machine Learning",
            max_results=1,
        )

    assert result["paper_count"] == 1
    assert result["papers"][0]["title"] == paper.title
    assert result["literature_review"] == "Sample literature review"
    assert result["hypothesis"] == "Sample hypothesis"

    mock_processor.assert_called_once_with(paper)
    mock_workflow.assert_called_once()

    context = mock_workflow.call_args.kwargs["paper_text"]
    assert "Evidence [1]" in context
    assert paper.title in context
    assert paper.url in context


def test_empty_research_topic():
    with pytest.raises(ValueError, match="Research topic cannot be empty"):
        run_research_from_papers("", max_results=3)


@pytest.mark.parametrize("max_results", [0, -1, 1.5, True, "3", None])
def test_invalid_paper_limit(max_results):
    with pytest.raises(ValueError, match="max_results"):
        run_research_from_papers(
            research_topic="Machine Learning",
            max_results=max_results,
        )


def test_empty_paper_text():
    with pytest.raises(ValueError, match="Paper text cannot be empty"):
        run_research_workflow(
            research_topic="Machine Learning",
            paper_text="",
        )


def test_no_papers_found():
    with (
        patch("services.paper_fetcher.search_all", return_value=[]),
        pytest.raises(ValueError, match="No research papers found"),
    ):
        run_research_from_papers(
            research_topic="Unknown Research Topic",
            max_results=3,
        )


def test_duplicate_papers_are_removed():
    paper = make_paper()
    record = make_processed_record(paper)

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper, paper],
        ),
        patch(
            "services.pdf_processor.process_paper",
            return_value=record,
        ) as mock_processor,
        patch(
            "agents.orchestrator.run_research_workflow",
            return_value=mock_research_result(),
        ),
    ):
        result = run_research_from_papers(
            research_topic="Machine Learning",
            max_results=2,
        )

    assert result["paper_count"] == 1
    assert len(result["papers"]) == 1
    mock_processor.assert_called_once_with(paper)


def test_paper_processing_failure_is_skipped():
    paper = make_paper("arxiv:5678")
    valid_paper = make_paper("arxiv:9012")

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper, valid_paper],
        ),
        patch(
            "services.pdf_processor.process_paper",
            side_effect=[
                RuntimeError("PDF processing failed"),
                make_processed_record(valid_paper),
            ],
        ),
        patch(
            "agents.orchestrator.run_research_workflow",
            return_value=mock_research_result(),
        ),
    ):
        result = run_research_from_papers(
            research_topic="Machine Learning",
            max_results=2,
        )

    assert result["paper_count"] == 1
    assert result["papers"][0]["paper_id"] == "arxiv:9012"


def test_all_paper_processing_failures_are_rejected():
    paper = make_paper()

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper],
        ),
        patch(
            "services.pdf_processor.process_paper",
            side_effect=RuntimeError("PDF processing failed"),
        ),
        pytest.raises(
            ValueError,
            match="No papers could be processed into usable text",
        ),
    ):
        run_research_from_papers(
            research_topic="Machine Learning",
            max_results=1,
        )


def test_papers_without_usable_text_are_skipped():
    paper = make_paper()
    record = make_processed_record(paper, full_text="  ")

    with (
        patch("services.paper_fetcher.search_all", return_value=[paper]),
        patch("services.pdf_processor.process_paper", return_value=record),
        pytest.raises(
            ValueError,
            match="No papers could be processed into usable text",
        ),
    ):
        run_research_from_papers(
            research_topic="Machine Learning",
            max_results=1,
        )
