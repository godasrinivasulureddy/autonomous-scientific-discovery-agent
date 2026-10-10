
from agents.literature_reviewer import review_literature
from agents.hypothesis_generator import generate_hypothesis
from agents.code_executor import execute_experiment


def run_research_workflow(
    research_topic: str,
    paper_text: str,
) -> dict:
    """Coordinate the scientific research agents."""

    if not research_topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if not paper_text.strip():
        raise ValueError("Paper text cannot be empty.")

    # Step 1: Review scientific literature
    literature_review = review_literature(
        research_topic=research_topic,
        paper_text=paper_text,
    )

    # Step 2: Generate a research hypothesis
    hypothesis = generate_hypothesis(
        research_topic=research_topic,
        literature_review=literature_review,
    )

    return {
        "research_topic": research_topic,
        "literature_review": literature_review,
        "hypothesis": hypothesis,
        "experiment": {
            "status": "not_executed",
            "reason": "An approved experiment and dataset are required.",
        },
    }


def run_approved_experiment(values: list[float]) -> dict:
    """Execute a predefined statistical experiment."""

    return execute_experiment(
        experiment_name="descriptive_statistics",
        values=values,
    )
