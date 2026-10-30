"""Week 3 Day 6 End-to-End System Integration Tests.

Validates the full multi-agent research pipeline:
1. Literature review and hypothesis generation with relevant memory context.
2. Controlled experiment execution and Docker isolation metadata.
3. Statistical Critic agent evaluation with confidence intervals and assumptions.
4. Memory Manager sliding window, token budgeting, and relevant history retrieval.
5. End-to-end safe failure handling for unapproved experiments or edge cases.
"""

from unittest.mock import patch
import pytest

from agents.orchestrator import (
    run_research_workflow,
    run_experiment_with_feedback,
    run_approved_experiment,
)
from agents.rag_orchestrator import run_rag_research
from agents.memory_manager import AgentMemoryManager
from agents.statistical_critic import evaluate_experiment_results


def test_e2e_full_multiagent_flow_with_memory_and_critic():
    """Verify complete multi-turn flow: Reviewer -> Hypothesis -> Execution -> Critic -> Memory."""
    memory = AgentMemoryManager(max_tokens=2000, max_entries=10)

    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="CRISPR Cas9 high-fidelity nucleases reduce off-target cleavage.",
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Engineered nuclease variant SpCas9-HF1 exhibits significantly lower indel rates at non-target loci.",
        ),
    ):
        result = run_research_workflow(
            research_topic="Precision Gene Editing",
            paper_text="Experimental assay measuring on-target vs off-target indel frequencies in HEK293T cells.",
            experiment_values=[0.12, 0.15, 0.14, 0.13, 0.16, 0.11],
            memory_manager=memory,
            enable_statistical_critic=True,
        )

    # 1. Pipeline result structure
    assert result["research_topic"] == "Precision Gene Editing"
    assert "CRISPR" in result["literature_review"]
    assert "SpCas9-HF1" in result["hypothesis"]
    assert result["experiment"]["status"] == "success"
    assert "mean" in result["experiment"]
    assert result["experiment"]["sample_size"] == 6

    # 2. Statistical Critic verification
    critic_res = result["statistical_critic_result"]
    assert critic_res["status"] == "evaluated"
    assert "confidence_interval" in critic_res
    assert isinstance(critic_res["confidence_interval"], list)
    assert len(critic_res["confidence_interval"]) == 2
    assert critic_res["confidence_interval"][0] < critic_res["confidence_interval"][1]
    assert "criticism" in critic_res

    # 3. Memory retention verification
    assert "memory_context" in result
    assert "LITERATURE_REVIEWER" in result["memory_context"]
    assert "HYPOTHESIS_GENERATOR" in result["memory_context"]
    assert "STATISTICAL_CRITIC" in result["memory_context"]

    # History entries check
    assert len(memory.history) >= 3
    retrieved = memory.retrieve_relevant_history("indel rates", top_k=2)
    assert len(retrieved) >= 1


def test_e2e_rag_research_with_memory_and_critic():
    """Verify RAG orchestrator connects vector context to memory and statistical critic."""
    memory = AgentMemoryManager(max_entries=8)

    sample_papers = [
        {
            "paper_id": "pubmed:3829102",
            "title": "Base Editing in Human T-Cells",
            "source": "pubmed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/3829102/",
            "text": "Cytidine base editors convert C:G to T:A without double-strand breaks.",
        }
    ]

    with (
        patch(
            "agents.langchain_workflow.review_literature",
            return_value="Cytidine base editors show high precision without double-strand breaks.",
        ),
        patch(
            "agents.langchain_workflow.generate_hypothesis",
            return_value="Base editor delivery leads to lower genomic rearrangements than standard nucleases.",
        ),
    ):
        rag_result = run_rag_research(
            research_topic="Base Editing Precision",
            search_papers=lambda *args, **kwargs: sample_papers,
            top_k=1,
            peer_reviewed_only=False,
            experiment_values=[2.1, 2.4, 2.3, 2.5, 2.2],
            memory_manager=memory,
            enable_statistical_critic=True,
        )

    assert rag_result["retrieval_count"] == 1
    assert rag_result["retrieved_papers"] == sample_papers
    assert rag_result["experiment"]["status"] == "success"
    assert rag_result["statistical_critic_result"]["status"] == "evaluated"
    assert len(memory.history) >= 3


def test_e2e_experiment_feedback_docker_and_critic_integration():
    """Verify run_experiment_with_feedback executes, scores, and critiques."""
    memory = AgentMemoryManager()
    values = [5.4, 5.6, 5.5, 5.8, 5.7, 5.3]

    result = run_experiment_with_feedback(
        values=values,
        use_docker=False,  # Unit test mode with code_executor
        memory_manager=memory,
    )

    assert result["experiment"]["status"] == "success"
    assert "metadata" in result["experiment"]
    assert result["experiment"]["metadata"]["execution_time_seconds"] >= 0.0

    assert "feedback" in result
    assert "reward" in result["feedback"]

    assert "statistical_critic" in result
    assert result["statistical_critic"]["status"] == "evaluated"
    assert "confidence_interval" in result["statistical_critic"]

    # History logged to memory
    roles = [entry["role"] for entry in memory.history]
    assert "code_executor" in roles
    assert "statistical_critic" in roles


def test_e2e_safe_failure_handling_with_invalid_experiment():
    """Verify unapproved or insufficient experiment values raise ValueError safely."""
    with pytest.raises(ValueError, match="At least two values are required"):
        run_approved_experiment(values=[42.0])


def test_e2e_direct_statistical_critic_evaluation():
    """Verify evaluate_experiment_results produces structured metrics and recommendations."""
    mock_experiment = {
        "status": "success",
        "sample_size": 10,
        "mean": 25.4,
        "standard_deviation": 1.8,
    }
    critic_output = evaluate_experiment_results(
        hypothesis="Target enzyme concentration accelerates catalytic rate beyond baseline.",
        experiment_result=mock_experiment,
        alpha=0.01,
    )

    assert critic_output["status"] == "evaluated"
    assert critic_output["significant"] is True
    assert critic_output["assumptions_met"] is True
    assert "confidence_interval" in critic_output
    assert isinstance(critic_output["confidence_interval"], list)
    assert len(critic_output["confidence_interval"]) == 2
    assert "criticism" in critic_output
    assert "recommendations" in critic_output
