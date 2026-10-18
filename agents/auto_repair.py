
"""Safely retry a restricted statistical experiment after code correction."""

import ast

from agents.code_debugger import (
    CodeCorrectionError,
    correct_python_code,
)
from services.docker_sandbox import run_in_sandbox


# Only this exact statistical program structure is approved.
APPROVED_IMPORTS = {"json", "statistics"}
APPROVED_CALLS = {
    "print", "len", "sum", "min", "max",
    "json.loads", "json.dumps",
    "mean", "stdev",
}


def validate_repair_policy(code: str) -> str:
    """Restrict generated code to a small statistical Python subset."""

    if not isinstance(code, str) or not code.strip():
        raise CodeCorrectionError("Code cannot be empty.")

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise CodeCorrectionError("Invalid Python syntax.") from error

    forbidden = (
        ast.ImportFrom,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.ClassDef,
        ast.Lambda,
        ast.While,
        ast.For,
        ast.AsyncFor,
        ast.With,
        ast.AsyncWith,
        ast.Try,
        ast.Raise,
        ast.Delete,
        ast.Global,
        ast.Nonlocal,
        ast.Attribute,
        ast.Subscript,
        ast.ListComp,
        ast.DictComp,
        ast.SetComp,
        ast.GeneratorExp,
        ast.Await,
        ast.Yield,
        ast.YieldFrom,
    )

    for node in ast.walk(tree):
        if isinstance(node, forbidden):
            # Attribute access is separately allowed only for json helpers.
            if isinstance(node, ast.Attribute):
                if not (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "json"
                    and node.attr in {"loads", "dumps"}
                ):
                    raise CodeCorrectionError(
                        "Disallowed attribute access."
                    )
            else:
                raise CodeCorrectionError(
                    f"Disallowed Python operation: {type(node).__name__}"
                )

        if isinstance(node, ast.Import):
            if any(
                alias.name not in APPROVED_IMPORTS or alias.asname
                for alias in node.names
            ):
                raise CodeCorrectionError("Unapproved import.")

        if isinstance(node, ast.Call):
            function = node.func

            if isinstance(function, ast.Name):
                name = function.id
            elif isinstance(function, ast.Attribute):
                name = f"{function.value.id}.{function.attr}"
            else:
                raise CodeCorrectionError("Unapproved function call.")

            if name not in APPROVED_CALLS:
                raise CodeCorrectionError(
                    f"Unapproved function call: {name}"
                )

    return code


def run_with_auto_repair(
    code: str,
    max_corrections: int = 2,
) -> dict:
    """Run approved code, repair errors, and stop after bounded retries."""

    if (
        not isinstance(max_corrections, int)
        or isinstance(max_corrections, bool)
        or not 0 <= max_corrections <= 2
    ):
        raise ValueError("max_corrections must be between 0 and 2.")

    current_code = validate_repair_policy(code)
    history = []

    for attempt in range(max_corrections + 1):
        result = run_in_sandbox(current_code)

        history.append({
            "attempt": attempt + 1,
            "status": result["status"],
            "stderr": result.get("stderr", ""),
        })

        if result["status"] == "success":
            return {
                "status": "success",
                "attempts": len(history),
                "result": result,
                "history": history,
            }

        if result["status"] == "timeout":
            break

        if attempt == max_corrections:
            break

        try:
            repaired_code = correct_python_code(
                original_code=current_code,
                error_message=result.get("stderr") or "Execution failed.",
            )
            current_code = validate_repair_policy(repaired_code)
        except (CodeCorrectionError, RuntimeError, ValueError) as error:
            return {
                "status": "repair_failed",
                "attempts": len(history),
                "error": str(error),
                "history": history,
            }

    return {
        "status": "failed",
        "attempts": len(history),
        "result": history[-1],
        "history": history,
    }
