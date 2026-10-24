
"""LangChain orchestration for research, experiments, and repair learning."""

from langchain_core.runnables import RunnableLambda

from agents.literature_reviewer import review_literature
from agents.hypothesis_generator import generate_hypothesis
from agents.code_executor import execute_experiment
from agents.repair_learning import run_and_learn


def run_langchain_research(
    topic: str,
    paper_text: str,
    experiment_values: list[float] | None = None,
    repair_code: str | None = None,
    repair_history_path: str | None = None,
) -> dict:
    """Run research agents and optionally execute bounded code repair."""

    if (
        not isinstance(topic, str)
        or not topic.strip()
        or not isinstance(paper_text, str)
        or not paper_text.strip()
    ):
        raise ValueError("Topic and paper text must not be empty.")

    if (repair_code is None) != (repair_history_path is None):
        raise ValueError(
            "repair_code and repair_history_path must be provided together."
        )

    if repair_code is not None and (
        not isinstance(repair_code, str) or not repair_code.strip()
    ):
        raise ValueError("Repair code must not be empty.")

    if repair_history_path is not None and (
        not isinstance(repair_history_path, str)
        or not repair_history_path.strip()
    ):
        raise ValueError("Repair history path must not be empty.")

    def literature_step(data: dict) -> dict:
        review = review_literature(
            data["topic"],
            data["paper_text"],
        )
        return {**data, "literature_review": review}

    
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
            experiment_result = {
                "status": "skipped",
                "reason": "No experiment data supplied.",
            }
        else:
            experiment_result = execute_experiment(
                experiment_name="descriptive_statistics",
                values=values,
            )

        output = {
            **data,
            "experiment_result": experiment_result,
        }

        if data["repair_code"] is not None:
            output["repair_learning_result"] = run_and_learn(
                code=data["repair_code"],
                history_path=data["repair_history_path"],
                max_corrections=2,
            )
        else:
            output["repair_learning_result"] = {
                "status": "skipped",
                "reason": "No repair program supplied.",
            }

        return output

    workflow = (
        RunnableLambda(literature_step)
        | RunnableLambda(hypothesis_step)
        | RunnableLambda(execution_step)
    )

    return workflow.invoke({
        "topic": topic,
        "paper_text": paper_text,
        "experiment_values": experiment_values,
        "repair_code": repair_code,
        "repair_history_path": repair_history_path,
    })
