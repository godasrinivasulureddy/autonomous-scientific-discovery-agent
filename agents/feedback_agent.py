
"""Evaluate experiment outcomes and calculate feedback rewards."""

import math


def evaluate_experiment(result: dict) -> dict:
    """Evaluate an approved experiment and assign a reward."""

    if not isinstance(result, dict):
        raise ValueError("Experiment result must be a dictionary.")

    if result.get("status") != "success":
        return {
            "reward": 0.0,
            "feedback": "Experiment did not complete successfully.",
            "accepted": False,
        }

    if result.get("experiment") != "descriptive_statistics":
        raise ValueError("Unsupported experiment type.")

    sample_size = result.get("sample_size")
    average = result.get("mean")
    deviation = result.get("standard_deviation")

    if (
        not isinstance(sample_size, int)
        or isinstance(sample_size, bool)
        or sample_size < 2
        or any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in (average, deviation)
        )
        or deviation < 0
    ):
        raise ValueError("Invalid experiment statistics.")

    # A simple heuristic reward, not a scientific validity score.
    reward = min(sample_size / 100, 1.0)

    return {
        "reward": round(reward, 3),
        "feedback": "Experiment completed with valid statistical output.",
        "accepted": True,
    }



def evaluate_repair_attempt(result: dict) -> dict:
    """Assign a bounded reward to a code-repair outcome."""

    if not isinstance(result, dict):
        raise ValueError("Repair result must be a dictionary.")

    status = result.get("status")
    attempts = result.get("attempts")

    if (
        not isinstance(attempts, int)
        or isinstance(attempts, bool)
        or attempts < 1
    ):
        raise ValueError("Repair attempts must be a positive integer.")

    if status == "success":
        # Reward successful repairs; prefer fewer attempts.
        reward = 1.0 / attempts
        return {
            "reward": round(reward, 3),
            "accepted": True,
            "feedback": (
                "Code repair succeeded."
                if attempts == 1
                else "Code repair succeeded after a retry."
            ),
        }

    if status in {"failed", "repair_failed"}:
        return {
            "reward": 0.0,
            "accepted": False,
            "feedback": "Code repair did not succeed.",
        }

    raise ValueError("Unsupported repair status.")
