
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch

import pytest

from services.docker_sandbox import run_in_sandbox


@pytest.fixture
def docker_available():
    """Mock Docker executable discovery for unit tests."""
    with patch(
        "services.docker_sandbox.shutil.which",
        return_value=r"C:\Docker\docker.exe",
    ):
        yield


def test_empty_code_rejected():
    with pytest.raises(ValueError):
        run_in_sandbox("   ")


def test_invalid_timeout_rejected():
    with pytest.raises(ValueError):
        run_in_sandbox("print('hello')", timeout=0)


def test_docker_security_restrictions(docker_available):
    with patch(
        "services.docker_sandbox.subprocess.run",
        return_value=CompletedProcess(
            args=[],
            returncode=0,
            stdout="hello\n",
            stderr="",
        ),
    ) as mock_run:
        result = run_in_sandbox("print('hello')")

    command = mock_run.call_args.args[0]

    assert "--network" in command
    assert command[command.index("--network") + 1] == "none"

    assert "--read-only" in command

    assert "--cap-drop" in command
    assert command[command.index("--cap-drop") + 1] == "ALL"

    assert "--security-opt" in command
    assert (
        command[command.index("--security-opt") + 1]
        == "no-new-privileges"
    )

    assert "--memory" in command
    assert command[command.index("--memory") + 1] == "128m"

    assert "--memory-swap" in command
    assert command[command.index("--memory-swap") + 1] == "128m"

    assert "--cpus" in command
    assert command[command.index("--cpus") + 1] == "0.5"

    assert "--pids-limit" in command
    assert command[command.index("--pids-limit") + 1] == "64"

    assert "--user" in command
    assert command[command.index("--user") + 1] == "10001:10001"

    assert "--tmpfs" in command

    assert result["status"] == "success"
    assert result["stdout"] == "hello\n"


def test_experiment_timeout(docker_available):
    with patch(
        "services.docker_sandbox.subprocess.run",
        side_effect=TimeoutExpired(cmd="docker", timeout=10),
    ):
        result = run_in_sandbox("while True: pass")

    assert result["status"] == "timeout"
    assert result["stdout"] == ""
    assert "time limit" in result["stderr"]


def test_docker_unavailable():
    with patch(
        "services.docker_sandbox.shutil.which",
        return_value=None,
    ):
        result = run_in_sandbox("print('hello')")

    assert result["status"] == "error"
    assert "Docker" in result["stderr"]


def test_timeout_removes_docker_container():
    """Verify that a timed-out container is force-removed."""

    with patch(
        "services.docker_sandbox.shutil.which",
        return_value=r"C:\Docker\docker.exe",
    ), patch(
        "services.docker_sandbox.subprocess.run",
        side_effect=[
            TimeoutExpired(cmd="docker", timeout=10),
            CompletedProcess(
                args=[],
                returncode=0,
                stdout="",
                stderr="",
            ),
        ],
    ) as mock_run:
        result = run_in_sandbox("while True: pass")

    assert result["status"] == "timeout"
    assert mock_run.call_count == 2

    run_command = mock_run.call_args_list[0].args[0]
    cleanup_command = mock_run.call_args_list[1].args[0]

    container_name = run_command[
        run_command.index("--name") + 1
    ]

    assert cleanup_command[1:] == [
        "rm", "-f", container_name
    ]
    assert cleanup_command[0].lower().endswith("docker.exe")


def test_output_is_limited_to_10000_characters(docker_available):
    with patch(
        "services.docker_sandbox.subprocess.run",
        return_value=CompletedProcess(
            args=[],
            returncode=0,
            stdout="A" * 15000,
            stderr="B" * 15000,
        ),
    ):
        result = run_in_sandbox("print('hello')")

    assert len(result["stdout"]) == 10000
    assert len(result["stderr"]) == 10000


def test_successful_execution_returns_output(docker_available):
    with patch(
        "services.docker_sandbox.subprocess.run",
        return_value=CompletedProcess(
            args=[],
            returncode=0,
            stdout="5\n",
            stderr="",
        ),
    ):
        result = run_in_sandbox("print(2 + 3)")

    assert result["status"] == "success"
    assert result["stdout"] == "5\n"
    assert result["stderr"] == ""


def test_failed_execution_returns_error(docker_available):
    with patch(
        "services.docker_sandbox.subprocess.run",
        return_value=CompletedProcess(
            args=[],
            returncode=1,
            stdout="",
            stderr="Execution failed",
        ),
    ):
        result = run_in_sandbox("raise Exception('test')")

    assert result["status"] == "error"
    assert result["stderr"] == "Execution failed"


def test_execute_experiment_in_docker_success():
    from agents.code_executor import execute_experiment_in_docker

    mock_output = '{"sample_size": 4, "mean": 25.0, "standard_deviation": 12.909944487358056}'

    with patch(
        "services.docker_sandbox.run_in_sandbox",
        return_value={
            "status": "success",
           "stdout": mock_output,
            "stderr": "",
        },
    ) as mock_sandbox:
        result = execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[10, 20, 30, 40],
        )

    assert result["status"] == "success"
    assert result["experiment"] == "descriptive_statistics"
    assert result["sample_size"] == 4
    assert result["mean"] == 25.0
    assert result["standard_deviation"] == pytest.approx(12.91, 0.01)
    mock_sandbox.assert_called_once()


def test_execute_experiment_in_docker_unapproved_rejected():
    from agents.code_executor import execute_experiment_in_docker

    with pytest.raises(ValueError, match="Experiment is not approved"):
        execute_experiment_in_docker(
            experiment_name="unapproved_ml_experiment",
            values=[1.0, 2.0],
        )


def test_execute_experiment_in_docker_invalid_values():
    from agents.code_executor import execute_experiment_in_docker

    with pytest.raises(ValueError, match="At least two finite numeric values"):
        execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[10],
        )

    with pytest.raises(ValueError, match="At least two finite numeric values"):
        execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[10, "string_val"],
        )

    with pytest.raises(ValueError, match="At least two finite numeric values"):
        execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[10, True, 30],
        )



def test_execute_experiment_in_docker_timeout_handling():
    from agents.code_executor import execute_experiment_in_docker

    with patch(
        "services.docker_sandbox.run_in_sandbox",
        return_value={
            "status": "timeout",
           "stdout": "",
            "stderr": "Experiment exceeded its time limit.",
        },
    ):
        result = execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[10, 20, 30],
        )

    assert result["status"] == "timeout"
    assert "time limit" in result["error"]
