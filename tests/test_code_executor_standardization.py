"""Unit tests for Code Executor standardization, execution metadata, and error handling."""

import pytest
from unittest.mock import patch
from agents.code_executor import execute_experiment, execute_experiment_in_docker


def test_execute_experiment_with_metadata():
    result = execute_experiment(
        experiment_name="descriptive_statistics",
        values=[10.0, 20.0, 30.0],
        include_metadata=True,
    )

    assert result["status"] == "success"
    assert result["sample_size"] == 3
    assert result["mean"] == 20.0
    assert result["standard_deviation"] == 10.0
    assert "metadata" in result
    assert result["metadata"]["docker_sandboxed"] is False
    assert result["metadata"]["execution_time_seconds"] >= 0.0
    assert result["error"] is None


def test_execute_experiment_in_docker_with_metadata():
    mock_stdout = '{"sample_size": 3, "mean": 15.0, "standard_deviation": 5.0}'
    with patch(
        "services.docker_sandbox.run_in_sandbox",
        return_value={"status": "success", "stdout": mock_stdout, "stderr": ""},
    ):
        result = execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[10.0, 15.0, 20.0],
            include_metadata=True,
        )

    assert result["status"] == "success"
    assert result["sample_size"] == 3
    assert result["mean"] == 15.0
    assert result["metadata"]["docker_sandboxed"] is True
    assert result["error"] is None


def test_execute_experiment_in_docker_error_metadata():
    with patch(
        "services.docker_sandbox.run_in_sandbox",
        return_value={"status": "error", "stdout": "", "stderr": "Container crashed"},
    ):
        result = execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[10.0, 20.0],
            include_metadata=True,
        )

    assert result["status"] == "error"
    assert result["error"] == "Container crashed"
    assert result["metadata"]["docker_sandboxed"] is True
