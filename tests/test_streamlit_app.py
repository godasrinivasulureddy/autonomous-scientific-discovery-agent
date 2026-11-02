"""Unit and integration tests for Streamlit app functions, citation extractor, and monitoring."""

from unittest.mock import MagicMock, patch
import pytest
from app import (
    render_results_section,
    execute_pipeline,
    extract_all_citations,
    render_workflow_summary_card,
)
from services.cost_tracker import ExecutionMetrics


def test_app_imports_cleanly():
    """Verify that app module loads without circular dependencies or missing symbols."""
    import app

    assert hasattr(app, "main")
    assert hasattr(app, "execute_pipeline")
    assert hasattr(app, "render_sidebar")
    assert hasattr(app, "render_topic_input_section")
    assert hasattr(app, "render_results_section")
    assert hasattr(app, "extract_all_citations")
    assert hasattr(app, "render_workflow_summary_card")


def test_extract_all_citations_aggregates_and_deduplicates():
    """Verify citations from multiple agent formats are unified and deduplicated."""
    sample_result = {
        "citation_metadata": [
            {
                "evidence_id": 1,
                "title": "AlphaFold Structure Prediction",
                "source": "Pinecone Vector Store",
                "url": "https://pubmed.ncbi.nlm.nih.gov/42906387/",
            }
        ],
        "citations": [
            {
                "title": "AlphaFold Structure Prediction",  # Duplicate title
                "source": "PubMed",
                "url": "https://pubmed.ncbi.nlm.nih.gov/42906387/",
            },
            {
                "title": "CRISPR-Cas9 Off-Target In Vitro Profiling",
                "source": "ArXiv",
                "url": "https://arxiv.org/abs/2301.0001",
            },
        ],
        "papers": [
            {
                "title": "A Full-Spectrum Generative Lead Discovery",
                "source": "PubMed",
                "url": "https://pubmed.ncbi.nlm.nih.gov/42950041/",
            }
        ],
    }

    citations = extract_all_citations(sample_result)
    assert len(citations) == 3
    titles = [c["title"] for c in citations]
    assert "AlphaFold Structure Prediction" in titles
    assert "CRISPR-Cas9 Off-Target In Vitro Profiling" in titles
    assert "A Full-Spectrum Generative Lead Discovery" in titles


def test_execute_pipeline_empty_topic_returns_none():
    """Verify pipeline rejects empty topic input gracefully."""
    config = {
        "workflow_mode": "Direct Literature Input / Text Context",
        "enable_statistical_critic": True,
        "enable_memory": True,
        "max_papers": 3,
        "peer_reviewed_only": False,
        "docker_timeout": 30,
    }
    inputs = {
        "research_topic": "   ",
        "manual_context": "Test context",
        "experiment_values": None,
        "pdf_file": None,
    }

    with patch("streamlit.error") as mock_error:
        result = execute_pipeline(config, inputs)
        assert result is None
        assert mock_error.called


@patch("app.run_research_workflow")
@patch("streamlit.progress")
def test_execute_pipeline_direct_mode_success(mock_progress, mock_workflow):
    """Verify direct literature mode coordinates workflow and returns metrics and stages."""
    mock_workflow.return_value = {
        "research_topic": "CRISPR off-target",
        "literature_review": "CRISPR literature summary",
        "hypothesis": "Engineered Cas9 reduces cleavage",
        "experiment": {"returncode": 0, "logs": "Success"},
        "statistical_critic_result": {"p_value": 0.01, "significant": True},
    }

    config = {
        "workflow_mode": "Direct Literature Input / Text Context",
        "enable_statistical_critic": True,
        "enable_memory": True,
        "max_papers": 3,
        "peer_reviewed_only": False,
        "docker_timeout": 30,
    }
    inputs = {
        "research_topic": "CRISPR off-target",
        "manual_context": "Sample literature context",
        "experiment_values": [12.0, 14.0],
        "pdf_file": None,
    }

    result = execute_pipeline(config, inputs)

    assert result is not None
    assert result["research_topic"] == "CRISPR off-target"
    assert "metrics" in result
    assert isinstance(result["metrics"], ExecutionMetrics)
    assert result["agent_stages"]["literature_reviewer"] == "completed"
    assert result["agent_stages"]["hypothesis_generator"] == "completed"
    assert result["agent_stages"]["code_executor"] == "completed"
    assert result["agent_stages"]["statistical_critic"] == "completed"


@patch("streamlit.tabs")
@patch("streamlit.markdown")
@patch("streamlit.info")
def test_render_results_section_display(mock_info, mock_markdown, mock_tabs):
    """Verify rendering results does not fail when inspecting result payload."""
    mock_tabs.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]

    sample_result = {
        "research_topic": "Quantum Computing",
        "workflow_mode": "RAG Semantic Retrieval (Pinecone)",
        "literature_review": "Review text",
        "hypothesis": "Hypothesis text",
        "citation_metadata": [{"title": "Quantum Paper", "source": "ArXiv", "url": "https://arxiv.org"}],
        "experiment": {
            "status": "success",
            "metadata": {"docker_sandboxed": True, "execution_time_seconds": 0.42},
        },
        "statistical_critic_result": {
            "p_value": 0.02,
            "significant": True,
            "test_name": "One-sample t-test",
            "confidence_interval": [12.1, 14.5],
            "criticism": "Evaluation passes alpha threshold.",
        },
        "multimodal_figures_count": 1,
        "visual_analyses": [
            {
                "reference_label": "Figure 1",
                "figure_type": "Bar Chart",
                "analysis": "Shows elevated fidelity.",
            }
        ],
        "metrics": ExecutionMetrics(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.000045,
            execution_time_seconds=1.2,
        ),
    }

    # Should run cleanly without raising exceptions
    render_results_section(sample_result)
    assert mock_tabs.called
