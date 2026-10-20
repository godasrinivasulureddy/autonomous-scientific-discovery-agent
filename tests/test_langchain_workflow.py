
from unittest.mock import patch

import pytest

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
    assert result["experiment_result"]["status"] == "skipped"
    assert result["repair_learning_result"]["status"] == "skipped"

    mock_review.assert_called_once()
    mock_hypothesis.assert_called_once()


def test_langchain_workflow_rejects_empty_input():
    with pytest.raises(ValueError):
        run_langchain_research("", "Research paper")


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
