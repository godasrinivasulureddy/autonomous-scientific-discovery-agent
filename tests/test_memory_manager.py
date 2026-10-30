"""Unit tests for AgentMemoryManager context-window, memory retention, and retrieval."""

import pytest
from agents.memory_manager import AgentMemoryManager


def test_memory_manager_initialization():
    memory = AgentMemoryManager(max_tokens=2000, max_entries=5)
    assert memory.max_tokens == 2000
    assert memory.max_entries == 5
    assert len(memory.history) == 0
    assert memory.running_summary == ""


def test_invalid_initialization_parameters():
    with pytest.raises(ValueError, match="max_tokens must be positive"):
        AgentMemoryManager(max_tokens=0)

    with pytest.raises(ValueError, match="max_entries must be positive"):
        AgentMemoryManager(max_entries=-1)


def test_add_interaction_validation():
    memory = AgentMemoryManager()

    with pytest.raises(ValueError, match="Role must be a non-empty string"):
        memory.add_interaction(role="", content="Test content")

    with pytest.raises(ValueError, match="Content must be a string"):
        memory.add_interaction(role="agent", content=123)  # type: ignore


def test_interaction_recording_and_context():
    memory = AgentMemoryManager()
    memory.add_interaction("literature_reviewer", "Found 3 papers on CRISPR-Cas9.")
    memory.add_interaction("hypothesis_generator", "Hypothesis: Cas9 modification increases efficiency.")

    assert len(memory.history) == 2
    context = memory.get_context()
    assert "LITERATURE_REVIEWER" in context
    assert "Found 3 papers on CRISPR-Cas9" in context
    assert "HYPOTHESIS_GENERATOR" in context
    assert "Hypothesis: Cas9 modification" in context


def test_memory_compression_on_entry_limit():
    memory = AgentMemoryManager(max_entries=4)

    for i in range(6):
        memory.add_interaction("agent", f"Step {i}: Hypothesis generated and finding verified.")

    # Should have compressed earlier entries
    assert len(memory.history) <= 4
    assert memory.running_summary != ""
    assert "Summary of past interactions" in memory.running_summary

    context = memory.get_context()
    assert "EXECUTIVE RESEARCH SUMMARY" in context
    assert "RECENT RESEARCH INTERACTIONS" in context


def test_memory_compression_on_token_limit():
    # Force compression via token budget
    memory = AgentMemoryManager(max_tokens=50, max_entries=10)

    long_text = "This is a detailed scientific finding discussing experiment results and evidence over multiple iterations. " * 3
    memory.add_interaction("reviewer", long_text)
    memory.add_interaction("generator", long_text)
    memory.add_interaction("executor", "Final result: mean is 42.0")

    assert memory.estimate_total_tokens() > 0
    context = memory.get_context()
    assert len(context) > 0


def test_memory_window_sliding_and_token_budget_preservation():
    """Verify that memory respects strict token budgets and produces compressed summaries without loss of key research findings."""
    memory = AgentMemoryManager(max_tokens=60, max_entries=4)

    memory.add_interaction("literature_reviewer", "Review: Discovered CRISPR-Cas9 variance in 10 clinical trials.")
    memory.add_interaction("hypothesis_generator", "Hypothesis: Cas9 modifications reduce off-target edits.")
    memory.add_interaction("code_executor", "Result: Descriptive statistics mean=14.2, std=1.8.")
    memory.add_interaction("statistical_critic", "Criticism: 95% CI is [12.8, 15.6], significance verified.")
    memory.add_interaction("agent", "Iteration 5: Next stage planned.")

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

    matches = memory.retrieve_relevant_history("protein thermal dynamics")
    assert len(matches) == 1
    assert "Protein folding" in matches[0]["content"]


def test_clear_memory():
    memory = AgentMemoryManager()
    memory.add_interaction("agent", "Temporary note")
    memory.compress()
    memory.clear()

    assert len(memory.history) == 0
    assert memory.running_summary == ""
    assert memory.get_context() == ""
