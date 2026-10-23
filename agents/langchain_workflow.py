
"""LangChain orchestration using existing scientific agents."""

from langchain_core.runnables import RunnableLambda

from agents.literature_reviewer import review_literature
from agents.hypothesis_generator import generate_hypothesis
from agents.code_executor import execute_experiment


def run_langchain_research(
    topic: str,
    paper_text: str,
    experiment_values: list[float] | None = None,
) -> dict:
    """Run three scientific agent roles in sequence."""

    if not topic.strip() or not paper_text.strip():
        raise ValueError("Topic and paper text must not be empty.")

    def literature_step(data: dict) -> dict:
        review = review_literature(
            data["topic"],
            data["paper_text"],
        )
        return {
            **data,
            "literature_review": review,
        }

    
    def hypothesis_step(data: dict) -> dict:
        hypothesis_input = (
            "LITERATURE REVIEW:\n"
            f"{data['literature_review']}\n\n"
            "ORIGINAL RETRIEVED EVIDENCE — use these evidence IDs "
            "and source details when supporting claims:\n"
            f"{data['paper_text']}"
        )

        hypothesis = generate_hypothesis(
            data["topic"],
            hypothesis_input,
        )
    

        return {
            **data,
            "hypothesis": hypothesis,
        }

    def execution_step(data: dict) -> dict:
        values = data["experiment_values"]

        if values is None:
            return {
                **data,
                "experiment_result": {
                    "status": "skipped",
                    "reason": "No experiment data supplied.",
                },
            }

        result = execute_experiment(
            experiment_name="descriptive_statistics",
            values=values,
        )

        return {
            **data,
            "experiment_result": result,
        }

    workflow = (
        RunnableLambda(literature_step)
        | RunnableLambda(hypothesis_step)
        | RunnableLambda(execution_step)
    )

    return workflow.invoke({
        "topic": topic,
        "paper_text": paper_text,
        "experiment_values": experiment_values,
    })
