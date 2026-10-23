
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



def test_hypothesis_receives_review_and_original_evidence():
    paper_text = (
        "Evidence [1]\n"
        "Title: Diabetes Prediction Study\n"
        "Source: Example Journal\n"
        "URL: https://example.org/diabetes-study\n"
        "Text: The study evaluates diabetes prediction."
    )

    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="Research summary",
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Research hypothesis",
        ) as mock_hypothesis,
    ):
        result = run_langchain_research(
            topic="Diabetes prediction",
            paper_text=paper_text,
        )

    mock_hypothesis.assert_called_once()
    args, _ = mock_hypothesis.call_args

    assert args[0] == "Diabetes prediction"
    assert "Research summary" in args[1]
    assert "Evidence [1]" in args[1]
    assert "https://example.org/diabetes-study" in args[1]
    assert result["hypothesis"] == "Research hypothesis"
