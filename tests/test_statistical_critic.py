"""Unit tests for Statistical Critic Agent and evaluation functions."""

from unittest.mock import patch
import pytest
from agents.statistical_critic import evaluate_experiment_results
from agents.code_executor import execute_experiment, execute_experiment_in_docker


def test_evaluate_experiment_results_valid():
    experiment_result = {
        "status": "success",
        "sample_size": 35,
        "mean": 10.5,
        "standard_deviation": 2.1,
    }
    criticism = evaluate_experiment_results(
        hypothesis="Treatment improves efficacy",
        experiment_result=experiment_result,
    )

    assert criticism["status"] == "evaluated"
    assert criticism["test_name"] == "descriptive"
    assert criticism["assumptions_met"] is True
    assert criticism["significant"] is True  # CI excludes 0
    assert len(criticism["confidence_interval"]) == 2
    assert criticism["confidence_interval"][0] < criticism["confidence_interval"][1]
    assert "95% CI" in criticism["criticism"]


def test_code_executor_integration_with_statistical_critic_success():
    """Verify that raw experiment results from execute_experiment pipe cleanly into evaluate_experiment_results."""
    exp_output = execute_experiment(
        experiment_name="descriptive_statistics",
        values=[12.0, 14.5, 15.0, 16.2, 17.8, 18.0],
        include_metadata=True,
    )

    critic_output = evaluate_experiment_results(
        hypothesis="Gene delivery increases target cell uptake significantly.",
        experiment_result=exp_output,
        alpha=0.05,
    )

    assert critic_output["status"] == "evaluated"
    assert critic_output["assumptions_met"] is True
    assert critic_output["significant"] is True
    assert len(critic_output["confidence_interval"]) == 2
    assert critic_output["confidence_interval"][0] < critic_output["confidence_interval"][1]
    assert "Sample size n=6" in critic_output["criticism"]


def test_docker_code_executor_integration_with_statistical_critic():
    """Verify that Docker sandbox results pipe seamlessly into the statistical critic evaluation."""
    mock_docker_stdout = '{"sample_size": 4, "mean": 25.0, "standard_deviation": 5.0}'
    with patch(
        "services.docker_sandbox.run_in_sandbox",
        return_value={"status": "success", "stdout": mock_docker_stdout, "stderr": ""},
    ):
        docker_result = execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[20.0, 25.0, 25.0, 30.0],
            include_metadata=True,
        )

    critic_output = evaluate_experiment_results(
        hypothesis="Algorithmic optimization reduces latency.",
        experiment_result=docker_result,
    )

    assert critic_output["status"] == "evaluated"
    assert critic_output["confidence_interval"] is not None
    assert critic_output["confidence_interval"][0] > 0


def test_evaluate_experiment_results_skipped():
    experiment_result = {
        "status": "skipped",
        "reason": "No experiment data supplied.",
    }
    criticism = evaluate_experiment_results(
        hypothesis="Hypothesis test",
        experiment_result=experiment_result,
    )

    assert criticism["status"] == "inconclusive"
    assert criticism["significant"] is False
    assert "skipped" in criticism["criticism"].lower()


def test_evaluate_experiment_results_error():
    experiment_result = {
        "status": "error",
        "error": "Timeout occurred in sandbox",
    }
    criticism = evaluate_experiment_results(
        hypothesis="Hypothesis test",
        experiment_result=experiment_result,
    )

    assert criticism["status"] == "failed"
    assert criticism["significant"] is False
    assert "failed" in criticism["criticism"].lower()


def test_agent_safe_failure_on_docker_timeout():
    """Verify that Docker execution timeouts are caught and passed as safe failure critic results."""
    mock_timeout_result = {
        "status": "timeout",
        "error": "Experiment exceeded its time limit.",
    }
    critic_output = evaluate_experiment_results(
        hypothesis="Long-running ML training convergence hypothesis.",
        experiment_result=mock_timeout_result,
    )

    assert critic_output["status"] == "failed"
    assert critic_output["significant"] is False
    assert "time limit" in critic_output["criticism"]
    assert "Debug execution code" in critic_output["recommendations"][0]


def test_evaluate_experiment_results_missing_data():
    experiment_result = {
        "status": "success",
        "sample_size": 1,
        "mean": 5.0,
        "standard_deviation": 0.0,
    }
    criticism = evaluate_experiment_results(
        hypothesis="Hypothesis test",
        experiment_result=experiment_result,
    )

    assert criticism["status"] == "inconclusive"
    assert "insufficient sample size" in criticism["criticism"].lower()


def test_evaluate_experiment_results_validation():
    with pytest.raises(ValueError, match="Hypothesis must be a non-empty string"):
        evaluate_experiment_results("", {"status": "success"})

    with pytest.raises(ValueError, match="experiment_result must be a dictionary"):
        evaluate_experiment_results("Valid hypothesis", "not a dict")  # type: ignore

    with pytest.raises(ValueError, match="alpha must be between 0 and 1 exclusive"):
        evaluate_experiment_results("Valid hypothesis", {"status": "success"}, alpha=1.5)
