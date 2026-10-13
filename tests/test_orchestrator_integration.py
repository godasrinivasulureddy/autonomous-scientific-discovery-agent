
from unittest.mock import patch

from agents.orchestrator import run_research_workflow


def test_research_workflow_integration():
    with patch(
        "agents.orchestrator.review_literature",
        return_value="Research gap: Limited evaluation data.",
    ) as mock_review, patch(
        "agents.orchestrator.generate_hypothesis",
        return_value="Hypothesis: More data improves accuracy.",
    ) as mock_hypothesis:

        result = run_research_workflow(
            research_topic="Machine Learning in Healthcare",
            paper_text="Sample scientific paper content.",
        )

    assert result["research_topic"] == "Machine Learning in Healthcare"
    assert result["literature_review"] == "Research gap: Limited evaluation data."
    assert result["hypothesis"] == "Hypothesis: More data improves accuracy."
    assert result["experiment"]["status"] == "not_executed"

    mock_review.assert_called_once_with(
        research_topic="Machine Learning in Healthcare",
        paper_text="Sample scientific paper content.",
    )

    mock_hypothesis.assert_called_once_with(
        research_topic="Machine Learning in Healthcare",
        literature_review="Research gap: Limited evaluation data.",
    )



def test_paper_search_agent_integration():
    from unittest.mock import patch
    from services.paper_fetcher import Paper
    from agents.orchestrator import run_research_from_papers

    sample_paper = Paper(
        paper_id="arxiv:1234",
        title="Machine Learning Research",
        abstract="This paper studies machine learning methods.",
        authors=["Test Author"],
        url="https://arxiv.org/abs/1234",
        published="2026-10-10",
        source="arxiv",
    )

    
    with patch(
        "services.paper_fetcher.search_all",
        return_value=[sample_paper],
    ), patch(
        "services.pdf_processor.process_paper",
        return_value={
            "title": "Machine Learning Research",
            "source": "arxiv",
            "url": "https://arxiv.org/abs/1234",
            "full_text": "Extracted scientific PDF content.",
        },
    ) as mock_processor, patch(
        "agents.orchestrator.run_research_workflow",


        
        return_value={
            "literature_review": "Sample literature review",
            "hypothesis": "Sample hypothesis",
        },
    ) as mock_workflow:

        result = run_research_from_papers(
            research_topic="Machine Learning",
            max_results=1,
        )



    
    assert result["paper_count"] == 1
    assert result["papers"][0]["title"] == "Machine Learning Research"
    assert result["literature_review"] == "Sample literature review"
    assert result["hypothesis"] == "Sample hypothesis"

    mock_workflow.assert_called_once()
    assert "Machine Learning Research" in (
        mock_workflow.call_args.kwargs["paper_text"]
    )
