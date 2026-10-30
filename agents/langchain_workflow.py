"""LangChain orchestration for research, experiments, statistical evaluation, and memory."""

from __future__ import annotations

from typing import Any
from langchain_core.runnables import RunnableLambda

from agents.literature_reviewer import review_literature
from agents.hypothesis_generator import generate_hypothesis
from agents.code_executor import execute_experiment
from agents.repair_learning import run_and_learn
from agents.statistical_critic import evaluate_experiment_results
from agents.memory_manager import AgentMemoryManager


def run_langchain_research(
    topic: str,
    paper_text: str,
    experiment_values: list[float] | None = None,
    repair_code: str | None = None,
    repair_history_path: str | None = None,
    memory_manager: AgentMemoryManager | None = None,
    enable_statistical_critic: bool = True,
) -> dict[str, Any]:
    """Run research agents with memory retention and statistical critic evaluation.

    Args:
        topic: Research topic query.
        paper_text: Context literature and retrieved evidence chunks.
        experiment_values: Numeric values for descriptive statistical experiment.
        repair_code: Optional buggy Python code for bounded repair testing.
        repair_history_path: Path to record repair iterations.
        memory_manager: Optional AgentMemoryManager instance for context retention.
        enable_statistical_critic: Whether to evaluate experiment results statistically.
    """
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

    def literature_step(data: dict[str, Any]) -> dict[str, Any]:
        review = review_literature(
            data["topic"],
            data["paper_text"],
        )
        if memory_manager:
            memory_manager.add_interaction(
                role="literature_reviewer",
                content=review,
                metadata={"topic": data["topic"]},
            )
        return {**data, "literature_review": review}

    def hypothesis_step(data: dict[str, Any]) -> dict[str, Any]:
        prior_context = ""
        if memory_manager and memory_manager.get_context():
            prior_context = f"\n\nPRIOR RESEARCH MEMORY:\n{memory_manager.get_context()}\n"

        hypothesis_input = (
            "LITERATURE REVIEW:\n"
            f"{data['literature_review']}\n\n"
            "ORIGINAL RETRIEVED EVIDENCE — use these evidence IDs "
            "and source details when supporting claims:\n"
            f"{data['paper_text']}"
            f"{prior_context}"
        )

        hypothesis = generate_hypothesis(
            data["topic"],
            hypothesis_input,
        )
        if memory_manager:
            memory_manager.add_interaction(
                role="hypothesis_generator",
                content=hypothesis,
                metadata={"topic": data["topic"]},
            )
        return {
            **data,
            "hypothesis": hypothesis,
        }

    def execution_step(data: dict[str, Any]) -> dict[str, Any]:
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

        # Step: Statistical Critic Evaluation
        if enable_statistical_critic:
            try:
                critic_result = evaluate_experiment_results(
                    hypothesis=data.get("hypothesis", ""),
                    experiment_result=experiment_result,
                )
            except Exception as exc:
                critic_result = {
                    "status": "error",
                    "error": str(exc),
                }
            output["statistical_critic_result"] = critic_result

            if memory_manager:
                memory_manager.add_interaction(
                    role="statistical_critic",
                    content=critic_result.get("criticism", str(critic_result)),
                    metadata={"status": critic_result.get("status")},
                )
        else:
            output["statistical_critic_result"] = {
                "status": "skipped",
                "reason": "Statistical critic is disabled.",
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

    result = workflow.invoke({
        "topic": topic,
        "paper_text": paper_text,
        "experiment_values": experiment_values,
        "repair_code": repair_code,
        "repair_history_path": repair_history_path,
    })

    if memory_manager:
        result["memory_context"] = memory_manager.get_context()

    return result
