
"""Bounded repair of a restricted statistical Python program."""

import ast

from agents.code_debugger import (
    CodeCorrectionError,
    correct_python_code,
)
from services.docker_sandbox import run_in_sandbox


SAFE_FUNCTIONS = {"print", "len", "sum", "min", "max"}
SAFE_VARIABLES = {"values", "result", "total", "average", "count"}
SAFE_CONSTANT_TYPES = (int, float, str, type(None))


def validate_repair_policy(code: str) -> str:
    """Accept only a small, explicitly defined Python subset."""

    if not isinstance(code, str) or not code.strip():
        raise CodeCorrectionError("Code cannot be empty.")

    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise CodeCorrectionError("Invalid Python syntax.") from error

    allowed_nodes = (
        ast.Module,
        ast.Expr,
        ast.Assign,
        ast.Name,
        ast.Load,
        ast.Store,
        ast.Call,
        ast.Constant,
        ast.List,
        ast.Tuple,
        ast.BinOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.UnaryOp,
        ast.USub,
    )

    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise CodeCorrectionError(
                f"Unapproved Python operation: {type(node).__name__}"
            )

        if isinstance(node, ast.Constant):
            if (
                isinstance(node.value, bool)
                or not isinstance(node.value, SAFE_CONSTANT_TYPES)
            ):
                raise CodeCorrectionError("Unapproved constant.")

        if isinstance(node, ast.Assign):
            if len(node.targets) != 1:
                raise CodeCorrectionError(
                    "Multiple assignment targets are not allowed."
                )

            target = node.targets[0]
            if not isinstance(target, ast.Name):
                raise CodeCorrectionError(
                    "Only simple variable assignments are allowed."
                )

            if target.id not in SAFE_VARIABLES:
                raise CodeCorrectionError(
                    f"Unapproved assignment target: {target.id}"
                )

        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                if node.id not in SAFE_VARIABLES:
                    raise CodeCorrectionError(
                        f"Unapproved variable: {node.id}"
                    )
            elif node.id not in SAFE_VARIABLES | SAFE_FUNCTIONS:
                raise CodeCorrectionError(
                    f"Unapproved name: {node.id}"
                )

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise CodeCorrectionError(
                    "Only direct approved function calls are allowed."
                )

            if node.func.id not in SAFE_FUNCTIONS:
                raise CodeCorrectionError(
                    f"Unapproved function call: {node.func.id}"
                )

    return code


def run_with_auto_repair(
    code: str,
    max_corrections: int = 2,
) -> dict:
    """Execute approved code with at most two corrections."""

    if (
        not isinstance(max_corrections, int)
        or isinstance(max_corrections, bool)
        or not 0 <= max_corrections <= 2
    ):
        raise ValueError(
            "max_corrections must be between 0 and 2."
        )

    current_code = validate_repair_policy(code)
    history = []

    for attempt in range(max_corrections + 1):
        result = run_in_sandbox(current_code)
        status = result.get("status")
        stderr = result.get("stderr", "")

        history.append({
            "attempt": attempt + 1,
            "status": status,
            "stderr": stderr,
        })

        if status == "success":
            return {
                "status": "success",
                "attempts": len(history),
                "result": result,
                "history": history,
            }

        # Do not attempt to repair timeouts or Docker failures.
        if (
            status != "error"
            or "Docker is not installed or unavailable" in stderr
            or "Cannot connect to the Docker daemon" in stderr
            or "Unable to find image" in stderr
        ):
            break

        if attempt == max_corrections:
            break

        try:
            repaired_code = correct_python_code(
                original_code=current_code,
                error_message=stderr or "Execution failed.",
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
