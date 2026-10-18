
"""Tests for bounded automatic code repair."""

from unittest.mock import patch

import pytest

from agents.auto_repair import (
    run_with_auto_repair,
    validate_repair_policy,
)
from agents.code_debugger import CodeCorrectionError


SAFE_CODE = "print(sum([1, 2, 3]))"


def test_approved_code():
    assert validate_repair_policy(SAFE_CODE) == SAFE_CODE


def test_reject_unapproved_import():
    with pytest.raises(CodeCorrectionError):
        validate_repair_policy("import os")


def test_reject_file_access():
    with pytest.raises(CodeCorrectionError):
        validate_repair_policy("open('secret.txt').read()")


def test_reject_infinite_loop():
    with pytest.raises(CodeCorrectionError):
        validate_repair_policy("while True:\n    pass")


@patch("agents.auto_repair.run_in_sandbox")
def test_success_first_attempt(mock_sandbox):
    mock_sandbox.return_value = {
        "status": "success",
        "stdout": "6\n",
        "stderr": "",
    }

    result = run_with_auto_repair(SAFE_CODE)

    assert result["status"] == "success"
    assert result["attempts"] == 1


@patch("agents.auto_repair.correct_python_code")
@patch("agents.auto_repair.run_in_sandbox")
def test_success_after_repair(mock_sandbox, mock_correct):
    mock_sandbox.side_effect = [
        {
            "status": "error",
            "stdout": "",
            "stderr": "NameError",
        },
        {
            "status": "success",
            "stdout": "6\n",
            "stderr": "",
        },
    ]
    mock_correct.return_value = SAFE_CODE

    result = run_with_auto_repair(SAFE_CODE)

    assert result["status"] == "success"
    assert result["attempts"] == 2
    mock_correct.assert_called_once()


@patch("agents.auto_repair.correct_python_code")
@patch("agents.auto_repair.run_in_sandbox")
def test_stop_after_retry_limit(mock_sandbox, mock_correct):
    mock_sandbox.return_value = {
        "status": "error",
        "stdout": "",
        "stderr": "NameError",
    }
    mock_correct.return_value = SAFE_CODE

    result = run_with_auto_repair(SAFE_CODE, max_corrections=2)

    assert result["status"] == "failed"
    assert result["attempts"] == 3
    assert mock_correct.call_count == 2


@patch("agents.auto_repair.correct_python_code")
@patch("agents.auto_repair.run_in_sandbox")
def test_timeout_does_not_retry(mock_sandbox, mock_correct):
    mock_sandbox.return_value = {
        "status": "timeout",
        "stdout": "",
        "stderr": "Experiment exceeded its time limit.",
    }

    result = run_with_auto_repair(SAFE_CODE)

    assert result["status"] == "failed"
    assert result["attempts"] == 1
    mock_correct.assert_not_called()


def test_reject_invalid_retry_limit():
    with pytest.raises(ValueError):
        run_with_auto_repair(SAFE_CODE, max_corrections=5)
