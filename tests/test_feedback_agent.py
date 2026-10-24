
import pytest

from agents.feedback_agent import ( evaluate_experiment, evaluate_repair_attempt,)


def test_successful_experiment():
    result = {
        "experiment": "descriptive_statistics",
        "status": "success",
        "sample_size": 50,
        "mean": 25.0,
        "standard_deviation": 5.0,
    }

    feedback = evaluate_experiment(result)

    assert feedback["reward"] == 0.5
    assert feedback["accepted"] is True
    assert feedback["feedback"]


def test_failed_experiment():
    feedback = evaluate_experiment({
        "experiment": "descriptive_statistics",
        "status": "error",
    })

    assert feedback["reward"] == 0.0
    assert feedback["accepted"] is False


def test_invalid_experiment_rejected():
    with pytest.raises(ValueError):
        evaluate_experiment({
            "experiment": "unknown_experiment",
            "status": "success",
            "sample_size": 10,
            "mean": 5.0,
            "standard_deviation": 1.0,
        })


def test_invalid_statistics_rejected():
    with pytest.raises(ValueError):
        evaluate_experiment({
            "experiment": "descriptive_statistics",
            "status": "success",
            "sample_size": 1,
            "mean": 5.0,
            "standard_deviation": 1.0,
        })


def test_reward_is_capped():
    feedback = evaluate_experiment({
        "experiment": "descriptive_statistics",
        "status": "success",
        "sample_size": 200,
        "mean": 25.0,
        "standard_deviation": 5.0,
    })

    assert feedback["reward"] == 1.0




def test_repair_success_on_first_attempt():
    feedback = evaluate_repair_attempt({
        "status": "success",
        "attempts": 1,
    })

    assert feedback["reward"] == 1.0
    assert feedback["accepted"] is True
    assert feedback["feedback"]


def test_repair_success_after_one_retry():
    feedback = evaluate_repair_attempt({
        "status": "success",
        "attempts": 2,
    })

    assert feedback["reward"] == 0.5
    assert feedback["accepted"] is True


def test_failed_repair_receives_zero_reward():
    feedback = evaluate_repair_attempt({
        "status": "failed",
        "attempts": 2,
    })

    assert feedback["reward"] == 0.0
    assert feedback["accepted"] is False


def test_invalid_repair_attempt_count():
    with pytest.raises(ValueError):
        evaluate_repair_attempt({
            "status": "success",
            "attempts": 0,
        })

