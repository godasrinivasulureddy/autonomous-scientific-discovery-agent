
from unittest.mock import patch

import pytest

from agents.langchain_workflow import run_langchain_research


def test_three_agents_execute_in_order():
    execution_order = []

    def mock_review(topic, paper_text):
        execution_order.append("literature")
        return "Research literature summary"

    def mock_hypothesis(topic, review):
        execution_order.append("hypothesis")
        return "Scientific hypothesis"

    def mock_executor(experiment_name, values):
        execution_order.append("executor")
        return {
            "status": "success",
            "experiment": experiment_name,
            "sample_size": len(values),
            "mean": 3.0,
        }

    with (
        patch(
            "agents.langchain_workflow.review_literature",
            side_effect=mock_review,
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            side_effect=mock_hypothesis,
        ),
        patch(
            "agents.langchain_workflow.execute_experiment",
            side_effect=mock_executor,
        ),
    ):
        result = run_langchain_research(
            topic="Machine Learning",
            paper_text="Scientific research paper",
            experiment_values=[2.0, 3.0, 4.0],
        )

    assert execution_order == [
        "literature",
        "hypothesis",
        "executor",
    ]
    assert result["literature_review"] == "Research literature summary"
    assert result["hypothesis"] == "Scientific hypothesis"
    assert result["experiment_result"]["status"] == "success"


def test_existing_two_argument_calls_remain_supported():
    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="Literature summary",
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Hypothesis",
        ),
    ):
        result = run_langchain_research(
            "Machine Learning",
            "Scientific research text",
        )

    assert result["experiment_result"]["status"] == "skipped"


def test_empty_topic_rejected():
    with pytest.raises(ValueError):
        run_langchain_research(
            "",
            "Scientific research text",
        )


def test_invalid_experiment_values_rejected():
    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="Literature summary",
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Hypothesis",
        ),
    ):
        with pytest.raises(ValueError):
            run_langchain_research(
                "Machine Learning",
                "Scientific research text",
                experiment_values=[1.0],
            )
