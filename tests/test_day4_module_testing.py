"""Day 4 Module Tests: Memory management behavior, Code Executor with statistical evaluation, and safe failure handling."""

from unittest.mock import patch
import pytest

from agents.memory_manager import AgentMemoryManager
from agents.statistical_critic import evaluate_experiment_results
from agents.code_executor import execute_experiment, execute_experiment_in_docker
from agents.langchain_workflow import run_langchain_research


# ---------------------------------------------------------------------------
# 1. Test Context-Window and Memory-Management Behavior
# ---------------------------------------------------------------------------

def test_memory_window_sliding_and_token_budget_preservation():
    """Verify that memory respects strict token budgets and produces compressed summaries without loss of key research findings."""
    memory = AgentMemoryManager(max_tokens=60, max_entries=4)

    # Add research steps
    memory.add_interaction("literature_reviewer", "Review: Discovered CRISPR-Cas9 variance in 10 clinical trials.")
    memory.add_interaction("hypothesis_generator", "Hypothesis: Cas9 modifications reduce off-target edits.")
    memory.add_interaction("code_executor", "Result: Descriptive statistics mean=14.2, std=1.8.")
    memory.add_interaction("statistical_critic", "Criticism: 95% CI is [12.8, 15.6], significance verified.")
    memory.add_interaction("agent", "Iteration 5: Next stage planned.")

    # Entries should stay constrained
    assert len(memory.history) <= 4
    assert memory.running_summary != ""

    context = memory.get_context()
    assert "EXECUTIVE RESEARCH SUMMARY" in context
    assert len(context) > 0


def test_memory_retrieval_handles_empty_and_special_character_queries():
    """Verify that memory retrieval is robust against edge-case queries."""
    memory = AgentMemoryManager()
    memory.add_interaction("literature_reviewer", "Protein folding dynamics under thermal stress.")

    assert memory.retrieve_relevant_history("") == []
    assert memory.retrieve_relevant_history("   ") == []
    assert memory.retrieve_relevant_history("!@#$%^&*()") == []

    # Valid keyword search
    matches = memory.retrieve_relevant_history("protein thermal dynamics")
    assert len(matches) == 1
    assert "Protein folding" in matches[0]["content"]


# ---------------------------------------------------------------------------
# 2. Test Code Executor Integration with Statistical Evaluation
# ---------------------------------------------------------------------------

def test_code_executor_integration_with_statistical_critic_success():
    """Verify that raw experiment results from execute_experiment pipe cleanly into evaluate_experiment_results."""
    exp_output = execute_experiment(
        experiment_name="descriptive_statistics",
        values=[12.0, 14.5, 15.0, 16.2, 17.8, 18.0],
        include_metadata=True,
    )

    critic_output = evaluate_experiment_results(
        hypothesis="Gene delivery increases target cell uptake significantly.",
        experiment_result=exp_output,
        alpha=0.05,
    )

    assert critic_output["status"] == "evaluated"
    assert critic_output["assumptions_met"] is True
    assert critic_output["significant"] is True
    assert len(critic_output["confidence_interval"]) == 2
    assert critic_output["confidence_interval"][0] < critic_output["confidence_interval"][1]
    assert "Sample size n=6" in critic_output["criticism"]


def test_docker_code_executor_integration_with_statistical_critic():
    """Verify that Docker sandbox results pipe seamlessly into the statistical critic evaluation."""
    mock_docker_stdout = '{"sample_size": 4, "mean": 25.0, "standard_deviation": 5.0}'
    with patch(
        "services.docker_sandbox.run_in_sandbox",
        return_value={"status": "success", "stdout": mock_docker_stdout, "stderr": ""},
    ):
        docker_result = execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=[20.0, 25.0, 25.0, 30.0],
            include_metadata=True,
        )

    critic_output = evaluate_experiment_results(
        hypothesis="Algorithmic optimization reduces latency.",
        experiment_result=docker_result,
    )

    assert critic_output["status"] == "evaluated"
    assert critic_output["confidence_interval"] is not None
    assert critic_output["confidence_interval"][0] > 0


# ---------------------------------------------------------------------------
# 3. Verify Agent Failures Are Handled Safely
# ---------------------------------------------------------------------------

def test_agent_safe_failure_on_unapproved_experiment():
    """Verify that unapproved experiment inputs raise a clear ValueError as enforced by safety policy."""
    with (
        patch("agents.langchain_workflow.review_literature", return_value="Literature text"),
        patch("agents.langchain_workflow.generate_hypothesis", return_value="Hypothesis text"),
    ):
        with pytest.raises(ValueError, match="At least two values are required"):
            run_langchain_research(
                topic="Neuroscience",
                paper_text="Neuroscience paper text",
                experiment_values=[1.0],  # Invalid sample size < 2
                enable_statistical_critic=True,
            )


def test_agent_safe_failure_on_docker_timeout():
    """Verify that Docker execution timeouts are caught and passed as safe failure critic results."""
    mock_timeout_result = {
        "status": "timeout",
        "error": "Experiment exceeded its time limit.",
    }
    critic_output = evaluate_experiment_results(
        hypothesis="Long-running ML training convergence hypothesis.",
        experiment_result=mock_timeout_result,
    )

    assert critic_output["status"] == "failed"
    assert critic_output["significant"] is False
    assert "time limit" in critic_output["criticism"]
    assert "Debug execution code" in critic_output["recommendations"][0]


def test_agent_safe_failure_on_malformed_critic_input():
    """Verify that empty hypotheses or corrupt dictionaries raise clean ValueErrors."""
    with pytest.raises(ValueError, match="Hypothesis must be a non-empty string"):
        evaluate_experiment_results(
            hypothesis="   ",
            experiment_result={"status": "success"},
        )

    with pytest.raises(ValueError, match="experiment_result must be a dictionary"):
        evaluate_experiment_results(
            hypothesis="Valid hypothesis",
            experiment_result="not-a-dict",  # type: ignore
        )
