"""Unit and integration tests for Streamlit app functions and components."""

from unittest.mock import MagicMock, patch
import pytest
from app import render_results_section, execute_pipeline
from services.cost_tracker import ExecutionMetrics


def test_app_imports_cleanly():
    """Verify that app module loads without circular dependencies or missing symbols."""
    import app

    assert hasattr(app, "main")
    assert hasattr(app, "execute_pipeline")
    assert hasattr(app, "render_sidebar")
    assert hasattr(app, "render_topic_input_section")
    assert hasattr(app, "render_results_section")


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
    """Verify direct literature mode coordinates workflow and returns metrics."""
    mock_workflow.return_value = {
        "research_topic": "CRISPR off-target",
        "literature_review": "CRISPR literature summary",
        "hypothesis": "Engineered Cas9 reduces cleavage",
        "experiment": {"returncode": 0, "logs": "Success"},
        "statistical_critic_result": {"p_value": 0.01, "is_statistically_significant": True},
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
    assert result["metrics"].total_tokens > 0
    assert result["metrics"].estimated_cost_usd > 0


@patch("streamlit.tabs")
@patch("streamlit.markdown")
@patch("streamlit.info")
def test_render_results_section_display(mock_info, mock_markdown, mock_tabs):
    """Verify rendering results does not fail when inspecting result payload."""
    mock_tabs.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock()]

    sample_result = {
        "research_topic": "Quantum Computing",
        "literature_review": "Review text",
        "hypothesis": "Hypothesis text",
        "citations": [{"title": "Quantum Paper", "source": "ArXiv", "url": "https://arxiv.org"}],
        "experiment": {"returncode": 0, "logs": "All tests passed"},
        "statistical_critic_result": {
            "p_value": 0.02,
            "is_statistically_significant": True,
            "test_performed": "One-sample t-test",
            "alpha": 0.05,
            "explanation": "P < 0.05",
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
