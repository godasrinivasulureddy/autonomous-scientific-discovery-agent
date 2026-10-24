
"""Unit tests for Week 2 code debugging."""

from unittest.mock import patch

import pytest

from agents.code_debugger import (
    CodeCorrectionError,
    correct_python_code,
    detect_execution_error,
    extract_python_code,
    validate_python_syntax,
)


def test_detect_execution_error():
    assert detect_execution_error(
        {"status": "error", "stderr": "NameError"}
    )
    assert detect_execution_error(
        {"status": "timeout", "stderr": "Timed out"}
    )
    assert not detect_execution_error(
        {"status": "success", "stderr": ""}
    )


def test_detect_execution_error_rejects_invalid_input():
    with pytest.raises(ValueError):
        detect_execution_error(None)


def test_validate_python_syntax():
    assert validate_python_syntax("print(1 + 1)") == "print(1 + 1)"


def test_invalid_python_syntax():
    with pytest.raises(CodeCorrectionError):
        validate_python_syntax("print(")


def test_extract_python_code():
    response = "```python\nprint('fixed')\n```"
    assert extract_python_code(response) == "print('fixed')"


def test_empty_gemini_response():
    with pytest.raises(CodeCorrectionError):
        extract_python_code("")


@patch("agents.code_debugger.generate_response")
def test_gemini_code_correction(mock_generate):
    mock_generate.return_value = "print('fixed')"

    result = correct_python_code(
        original_code="print('broken'",
        error_message="SyntaxError: '(' was never closed",
    )

    assert result == "print('fixed')"
    mock_generate.assert_called_once()


@patch("agents.code_debugger.generate_response")
def test_gemini_invalid_correction(mock_generate):
    mock_generate.return_value = "print("

    with pytest.raises(CodeCorrectionError):
        correct_python_code(
            original_code="print('broken'",
            error_message="SyntaxError",
        )
