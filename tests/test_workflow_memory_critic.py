"""Unit tests for LangChain workflow integration with memory manager and statistical critic."""

from unittest.mock import patch
import pytest
from agents.langchain_workflow import run_langchain_research
from agents.memory_manager import AgentMemoryManager


def test_workflow_with_memory_and_statistical_critic():
    memory = AgentMemoryManager(max_entries=10)

    with (
        patch("agents.langchain_workflow.review_literature", return_value="Review of machine learning."),
        patch("agents.langchain_workflow.generate_hypothesis", return_value="Hypothesis on model optimization."),
    ):
        result = run_langchain_research(
            topic="Model Optimization",
            paper_text="Sample paper content.",
            experiment_values=[10.0, 12.0, 14.0, 16.0],
            memory_manager=memory,
            enable_statistical_critic=True,
        )

    assert result["literature_review"] == "Review of machine learning."
    assert result["hypothesis"] == "Hypothesis on model optimization."
    assert result["experiment_result"]["status"] == "success"

    # Verify Statistical Critic Agent connected
    assert "statistical_critic_result" in result
    assert result["statistical_critic_result"]["status"] == "evaluated"
    assert result["statistical_critic_result"]["significant"] is True
    assert "confidence_interval" in result["statistical_critic_result"]

    # Verify Memory Manager recorded turns
    assert "memory_context" in result
    assert "LITERATURE_REVIEWER" in result["memory_context"]
    assert "HYPOTHESIS_GENERATOR" in result["memory_context"]
    assert "STATISTICAL_CRITIC" in result["memory_context"]


def test_workflow_with_statistical_critic_disabled():
    with (
        patch("agents.langchain_workflow.review_literature", return_value="Review"),
        patch("agents.langchain_workflow.generate_hypothesis", return_value="Hypothesis"),
    ):
        result = run_langchain_research(
            topic="Test Topic",
            paper_text="Test paper",
            experiment_values=[5.0, 10.0],
            enable_statistical_critic=False,
        )

    assert result["statistical_critic_result"]["status"] == "skipped"


def test_relevant_history_retrieval_in_memory():
    memory = AgentMemoryManager()
    memory.add_interaction("literature_reviewer", "Focusing on CRISPR gene editing and Cas9 accuracy.")
    memory.add_interaction("hypothesis_generator", "Cas9 base-editor yields lower off-target frequency.")
    memory.add_interaction("code_executor", "Statistical run on model parameters.")

    relevant = memory.retrieve_relevant_history("CRISPR Cas9 accuracy", top_k=2)
    assert len(relevant) >= 1
    assert any("CRISPR" in item["content"] for item in relevant)

    context_filtered = memory.get_context(relevant_query="CRISPR")
    assert "CRISPR" in context_filtered
