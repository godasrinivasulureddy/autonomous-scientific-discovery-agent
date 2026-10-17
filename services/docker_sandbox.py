
"""Run Python experiments in a resource-restricted Docker container."""

import subprocess
import uuid

SANDBOX_IMAGE = "scientific-agent-sandbox:latest"


def run_in_sandbox(code: str, timeout: int = 10) -> dict:
    """Execute Python code inside a resource-limited Docker container."""

    if not isinstance(code, str) or not code.strip():
        raise ValueError("Python code cannot be empty.")

    if (
        not isinstance(timeout, int)
        or isinstance(timeout, bool)
        or not 1 <= timeout <= 30
    ):
        raise ValueError("Timeout must be between 1 and 30 seconds.")

    # Give each container a unique name for cleanup.
    container_name = f"scientific-sandbox-{uuid.uuid4().hex}"

    command = [
        "docker", "run",
        "--rm",
        "--name", container_name,
        "--interactive",
        "--network", "none",
        "--read-only",
        "--memory", "128m",
        "--memory-swap", "128m",
        "--cpus", "0.5",
        "--pids-limit", "64",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "10001:10001",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
        SANDBOX_IMAGE,
    ]

    try:
        result = subprocess.run(
            command,
            input=code,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    except subprocess.TimeoutExpired:
        # Best-effort cleanup if execution exceeds the time limit.
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass

        return {
            "status": "timeout",
            "stdout": "",
            "stderr": "Experiment exceeded its time limit.",
        }

    except FileNotFoundError:
        return {
            "status": "error",
            "stdout": "",
            "stderr": "Docker is not installed or unavailable.",
        }

    return {
        "status": "success" if result.returncode == 0 else "error",
        "stdout": result.stdout[:10000],
        "stderr": result.stderr[:10000],
    }
