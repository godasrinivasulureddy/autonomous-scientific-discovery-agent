
import pytest

from agents.orchestrator import run_approved_experiment
from agents.code_executor import execute_experiment


def test_approved_experiment():
    result = run_approved_experiment([10, 20, 30, 40])

    assert result["status"] == "success"
    assert result["sample_size"] == 4
    assert result["mean"] == 25


def test_unapproved_experiment():
    with pytest.raises(ValueError):
        execute_experiment(
            experiment_name="unknown_experiment",
            values=[10, 20, 30],
        )


def test_insufficient_data():
    with pytest.raises(ValueError):
        run_approved_experiment([10])
