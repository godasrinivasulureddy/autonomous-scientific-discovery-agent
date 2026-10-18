
"""Bounded, syntax-checked code correction using Gemini."""

import ast
import re

from services.gemini_service import generate_response

class CodeCorrectionError(Exception):
    """Raised when a proposed code correction cannot be accepted."""


def detect_execution_error(result: dict) -> bool:
    """Identify a failed sandbox execution."""

    if not isinstance(result, dict):
        raise ValueError("Execution result must be a dictionary.")

    return result.get("status") in {"error", "timeout"}


def validate_python_syntax(code: str) -> str:
    """Validate Python syntax without executing the code."""

    if not isinstance(code, str) or not code.strip():
        raise CodeCorrectionError("Corrected Python code is empty.")

    try:
        ast.parse(code)
    except SyntaxError as exc:
        raise CodeCorrectionError(
            f"Corrected Python code has invalid syntax: {exc}"
        ) from exc

    return code


def extract_python_code(response: str) -> str:
    """Extract Python code from a Gemini response."""

    if not isinstance(response, str) or not response.strip():
        raise CodeCorrectionError("Gemini returned an empty response.")

    match = re.search(
        r"```(?:python)?\s*\n(.*?)```",
        response,
        flags=re.DOTALL | re.IGNORECASE,
    )

    code = match.group(1).strip() if match else response.strip()

    return validate_python_syntax(code)


def correct_python_code(
    original_code: str,
    error_message: str,
) -> str:
    """Ask Gemini to suggest a syntax-checked correction."""

    if not isinstance(original_code, str) or not original_code.strip():
        raise ValueError("Original Python code cannot be empty.")

    if not isinstance(error_message, str) or not error_message.strip():
        raise ValueError("An execution error message is required.")

    prompt = (
        "You are debugging a controlled scientific Python experiment.\n"
        "Fix only the reported error.\n"
        "Return only corrected Python code, without explanations.\n"
        "Do not add network calls, subprocesses, file operations, "
        "package installation, or shell commands.\n\n"
        f"Original code:\n{original_code}\n\n"
        f"Execution error:\n{error_message}\n"
    )

    response = generate_response(prompt)

    return extract_python_code(response)
