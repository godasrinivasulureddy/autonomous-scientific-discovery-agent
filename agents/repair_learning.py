
"""Connect code-repair outcomes to persistent reward history."""

from pathlib import Path

from agents.auto_repair import run_with_auto_repair
from agents.experiment_selector import ExperimentSelector
from agents.feedback_agent import evaluate_repair_attempt


REPAIR_STRATEGY = "code_repair"


def run_and_learn(
    code: str,
    history_path: str | Path,
    max_corrections: int = 2,
) -> dict:
    """Run auto-repair, score its outcome, and save its reward."""

    selector = ExperimentSelector(exploration_rate=0.0)
    selector.load(str(history_path))

    result = run_with_auto_repair(
        code,
        max_corrections=max_corrections,
    )

    feedback = evaluate_repair_attempt({
        "status": result["status"],
        "attempts": result["attempts"],
    })

    selector.update(REPAIR_STRATEGY, feedback["reward"])
    selector.save(str(history_path))

    return {
        "result": result,
        "feedback": feedback,
        "average_repair_reward": selector.average_reward(
            REPAIR_STRATEGY
        ),
    }
