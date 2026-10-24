
from statistics import mean, stdev
import time
from typing import Any


def execute_experiment(
    experiment_name: str,
    values: list[float],
    include_metadata: bool = False,
) -> dict[str, Any]:
    """Run an approved statistical experiment."""

    start_time = time.time()

    if experiment_name != "descriptive_statistics":
        raise ValueError("Experiment is not approved.")

    if len(values) < 2:
        raise ValueError("At least two values are required.")

    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        for value in values
    ):
        raise ValueError("All values must be numeric.")

    sample_size = len(values)
    mean_val = mean(values)
    std_val = stdev(values)
    exec_duration = time.time() - start_time

    res: dict[str, Any] = {
        "experiment": experiment_name,
        "sample_size": sample_size,
        "mean": mean_val,
        "standard_deviation": std_val,
        "status": "success",
    }

    if include_metadata:
        res["metadata"] = {
            "execution_time_seconds": round(exec_duration, 4),
            "docker_sandboxed": False,
            "sample_size": sample_size,
        }
        res["error"] = None

    return res




def execute_experiment_in_docker(
    experiment_name: str,
    values: list[float],
    include_metadata: bool = False,
) -> dict[str, Any]:
    """Run an approved statistical experiment inside Docker."""

    import json
    import math

    from services.docker_sandbox import run_in_sandbox

    start_time = time.time()

    if experiment_name != "descriptive_statistics":
        raise ValueError("Experiment is not approved.")

    if (
        len(values) < 2
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in values
        )
    ):
        raise ValueError("At least two finite numeric values are required.")

    # Serialize validated numeric values rather than accepting generated code.
    safe_values = json.dumps(values)

    code = (
        "import json\n"
        "from statistics import mean, stdev\n"
        f"values = json.loads({safe_values!r})\n"
        "print(json.dumps({"
        "'sample_size': len(values), "
        "'mean': mean(values), "
        "'standard_deviation': stdev(values)"
        "}))\n"
    )

    result = run_in_sandbox(code)
    exec_duration = time.time() - start_time

    if result["status"] != "success":
        res = {
            "experiment": experiment_name,
            "status": result["status"],
            "error": result["stderr"],
        }
        if include_metadata:
            res["metadata"] = {
                "execution_time_seconds": round(exec_duration, 4),
                "docker_sandboxed": True,
            }
        return res

    statistics = json.loads(result["stdout"])

    res = {
        "experiment": experiment_name,
        "sample_size": statistics["sample_size"],
        "mean": statistics["mean"],
        "standard_deviation": statistics["standard_deviation"],
        "status": "success",
    }

    if include_metadata:
        res["metadata"] = {
            "execution_time_seconds": round(exec_duration, 4),
            "docker_sandboxed": True,
            "sample_size": statistics["sample_size"],
        }
        res["error"] = None

    return res
