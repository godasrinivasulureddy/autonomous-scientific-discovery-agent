import pytest
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


def test_langchain_workflow_preserves_multiple_source_citations():
    paper_text = (
        "Evidence [1]\n"
        "Title: Diabetes Prediction Study\n"
        "URL: https://example.org/diabetes\n"
        "Text: Machine learning supports diabetes prediction.\n\n"
        "Evidence [2]\n"
        "Title: Clinical Risk Assessment Study\n"
        "URL: https://example.org/clinical-risk\n"
        "Text: Clinical factors can support risk assessment."
    )

    literature_review = (
        "Evidence [1] discusses diabetes prediction.\n"
        "Evidence [2] discusses clinical risk assessment."
    )

    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value=literature_review,
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Hypothesis supported by Evidence [1] and Evidence [2].",
        ) as mock_hypothesis,
    ):
        result = run_langchain_research(
            topic="Diabetes risk prediction",
            paper_text=paper_text,
        )

    args, _ = mock_hypothesis.call_args
    hypothesis_input = args[1]

    assert literature_review in hypothesis_input
    assert "Evidence [1]" in hypothesis_input
    assert "Evidence [2]" in hypothesis_input
    assert "https://example.org/diabetes" in hypothesis_input
    assert "https://example.org/clinical-risk" in hypothesis_input
    assert "Evidence [1]" in result["hypothesis"]
    assert "Evidence [2]" in result["hypothesis"]


def test_workflow_integrates_repair_learning():
    repair_outcome = {
        "result": {
            "status": "success",
            "attempts": 2,
        },
        "feedback": {
            "reward": 0.5,
            "accepted": True,
            "feedback": "Code repair succeeded after a retry.",
        },
        "average_repair_reward": 0.5,
    }

    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="Research summary",
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Research hypothesis",
        ),
        patch(
            "agents.langchain_workflow.run_and_learn",
            return_value=repair_outcome,
        ) as mock_repair,
    ):
        result = run_langchain_research(
            topic="Diabetes prediction",
            paper_text="Machine learning research paper.",
            repair_code="print(sum([10, 20, 30]))",
            repair_history_path="repair_rewards.json",
        )

    mock_repair.assert_called_once_with(
        code="print(sum([10, 20, 30]))",
        history_path="repair_rewards.json",
        max_corrections=2,
    )
    assert result["repair_learning_result"] == repair_outcome
    assert (
        result["repair_learning_result"]["feedback"]["reward"]
        == 0.5
    )


def test_workflow_rejects_incomplete_repair_configuration():
    with pytest.raises(ValueError):
        run_langchain_research(
            topic="Diabetes prediction",
            paper_text="Machine learning research paper.",
            repair_code="print(sum([1, 2, 3]))",
        )

    with pytest.raises(ValueError):
        run_langchain_research(
            topic="Diabetes prediction",
            paper_text="Machine learning research paper.",
            repair_history_path="repair_rewards.json",
        )


def test_workflow_skips_repair_when_not_requested():
    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="Research summary",
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Research hypothesis",
        ),
        patch(
            "agents.langchain_workflow.run_and_learn",
        ) as mock_repair,
    ):
        result = run_langchain_research(
            topic="Diabetes prediction",
            paper_text="Machine learning research paper.",
        )

    mock_repair.assert_not_called()
    assert result["repair_learning_result"]["status"] == "skipped"
