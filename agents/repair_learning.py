
"""Connect code-repair outcomes to persistent reward history."""

import json
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
    """Run auto-repair, score its outcome, and save its history."""

    history_path = Path(history_path)

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

    # Preserve the existing reward-history format.
    selector.update(REPAIR_STRATEGY, feedback["reward"])
    selector.save(str(history_path))

    # Store a separate record for each repair run.
    run_history_path = history_path.with_name(
        f"{history_path.stem}_runs.json"
    )
    run_history_path.parent.mkdir(parents=True, exist_ok=True)

    if run_history_path.exists():
        with run_history_path.open("r", encoding="utf-8") as file:
            run_history = json.load(file)

        if not isinstance(run_history, list):
            raise ValueError("Invalid repair run history format.")
    else:
        run_history = []

    run_record = {
        "strategy": REPAIR_STRATEGY,
        "status": result["status"],
        "attempts": result["attempts"],
        "reward": feedback["reward"],
        "accepted": feedback["accepted"],
        "history": result.get("history", []),
    }

    run_history.append(run_record)

    with run_history_path.open("w", encoding="utf-8") as file:
        json.dump(run_history, file, indent=2)

    return {
        "result": result,
        "feedback": feedback,
        "average_repair_reward": selector.average_reward(
            REPAIR_STRATEGY
        ),
        "repair_record": run_record,
        "repair_history_path": str(run_history_path),
    }
