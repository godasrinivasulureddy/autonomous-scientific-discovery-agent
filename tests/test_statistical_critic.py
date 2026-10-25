"""Unit tests for Statistical Critic Agent and evaluation functions."""

import pytest
from agents.statistical_critic import evaluate_experiment_results


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
