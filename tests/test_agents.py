
import pytest
from unittest.mock import patch

from agents.orchestrator import run_approved_experiment
from agents.code_executor import execute_experiment
from agents.hypothesis_generator import generate_hypothesis


def test_approved_experiment():
    result = run_approved_experiment([10, 20, 30, 40])

    assert result["status"] == "success"
    assert result["sample_size"] == 4
    assert result["mean"] == 25


def test_unapproved_experiment():
    with pytest.raises(ValueError):
        execute_experiment(
            experiment_name="unknown_experiment",
            values=[10, 20, 30],
        )


def test_insufficient_data():
    with pytest.raises(ValueError):
        run_approved_experiment([10])


def test_standard_deviation():
    result = run_approved_experiment([10, 20, 30])

    assert result["status"] == "success"
    assert result["sample_size"] == 3
    assert result["mean"] == 20
    assert result["standard_deviation"] == pytest.approx(10.0)


@pytest.mark.parametrize(
    "invalid_values",
    [
        [10, "twenty", 30],
        [10, None, 30],
        [10, True, 30],
    ],
)
def test_invalid_experiment_values(invalid_values):
    with pytest.raises(ValueError, match="All values must be numeric"):
        run_approved_experiment(invalid_values)


@pytest.mark.parametrize(
    "research_topic",
    ["", "   ", None, 123],
)
def test_hypothesis_rejects_invalid_topic(research_topic):
    with pytest.raises(ValueError, match="Research topic"):
        generate_hypothesis(research_topic, "Relevant literature.")


@pytest.mark.parametrize(
    "literature_review",
    ["", "   ", None, 123],
)
def test_hypothesis_rejects_invalid_literature(literature_review):
    with pytest.raises(ValueError, match="Literature review"):
        generate_hypothesis("Research topic", literature_review)


def test_hypothesis_uses_literature_and_returns_response():
    expected = "Hypothesis: Treatment A improves outcome B."

    with patch(
        "agents.hypothesis_generator.generate_response",
        return_value=f"  {expected}  ",
    ) as mock_generate:
        result = generate_hypothesis(
            research_topic="Treatment effectiveness",
            literature_review="Evidence [1] reports an association.",
        )

    assert result == expected

    prompt = mock_generate.call_args.args[0]
    assert "Treatment effectiveness" in prompt
    assert "Evidence [1] reports an association." in prompt
    assert "Never invent papers" in prompt
    assert "Supporting Evidence" in prompt


@pytest.mark.parametrize("response", ["", "   ", None, 123])
def test_hypothesis_rejects_empty_or_invalid_response(response):
    with patch(
        "agents.hypothesis_generator.generate_response",
        return_value=response,
    ):
        with pytest.raises(ValueError, match="empty response"):
            generate_hypothesis(
                "Research topic",
                "Relevant literature.",
            )
