
from unittest.mock import patch

from agents.langchain_workflow import run_langchain_research


def test_langchain_workflow():
    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="Research summary",
        ) as mock_review,
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Research hypothesis",
        ) as mock_hypothesis,
    ):
        result = run_langchain_research(
            topic="Diabetes prediction",
            paper_text="Machine learning research paper.",
        )

    assert result["literature_review"] == "Research summary"
    assert result["hypothesis"] == "Research hypothesis"

    mock_review.assert_called_once()
    mock_hypothesis.assert_called_once()


def test_langchain_workflow_rejects_empty_input():
    try:
        run_langchain_research("", "Research paper")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError for empty topic")
