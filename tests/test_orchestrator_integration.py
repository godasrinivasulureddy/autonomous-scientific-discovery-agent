
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
