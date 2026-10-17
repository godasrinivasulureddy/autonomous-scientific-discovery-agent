
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch

import pytest

from services.docker_sandbox import run_in_sandbox


def test_empty_code_rejected():
    with pytest.raises(ValueError):
        run_in_sandbox("   ")


def test_invalid_timeout_rejected():
    with pytest.raises(ValueError):
        run_in_sandbox("print('hello')", timeout=0)


def test_docker_security_restrictions():
    with patch(
        "services.docker_sandbox.subprocess.run",
        return_value=CompletedProcess(
            args=[], returncode=0, stdout="hello\n", stderr=""
        ),
    ) as mock_run:
        result = run_in_sandbox("print('hello')")

    command = mock_run.call_args.args[0]

    assert "--network" in command
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command
    assert "--cap-drop" in command
    assert "ALL" in command
    assert "--security-opt" in command
    assert "no-new-privileges" in command
    assert "--memory" in command
    assert "--cpus" in command
    assert "--pids-limit" in command
    assert result["status"] == "success"


def test_experiment_timeout():
    with patch(
        "services.docker_sandbox.subprocess.run",
        side_effect=TimeoutExpired(cmd="docker", timeout=10),
    ):
        result = run_in_sandbox("while True: pass")

    assert result["status"] == "timeout"


def test_docker_unavailable():
    with patch(
        "services.docker_sandbox.subprocess.run",
        side_effect=FileNotFoundError(),
    ):
        result = run_in_sandbox("print('hello')")

    assert result["status"] == "error"
    assert "Docker" in result["stderr"]



def test_timeout_removes_docker_container():
    """Verify that a timed-out container is force-removed."""

    with patch(
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

    assert cleanup_command == [
        "docker", "rm", "-f", container_name
    ]

