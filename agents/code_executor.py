
from statistics import mean, stdev


def execute_experiment(
    experiment_name: str,
    values: list[float],
) -> dict:
    """Run an approved statistical experiment."""

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

    return {
        "experiment": experiment_name,
        "sample_size": len(values),
        "mean": mean(values),
        "standard_deviation": stdev(values),
        "status": "success",
    }




def execute_experiment_in_docker(
    experiment_name: str,
    values: list[float],
) -> dict:
    """Run an approved statistical experiment inside Docker."""

    import json
    import math

    from services.docker_sandbox import run_in_sandbox

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

    if result["status"] != "success":
        return {
            "experiment": experiment_name,
            "status": result["status"],
            "error": result["stderr"],
        }

    statistics = json.loads(result["stdout"])

    return {
        "experiment": experiment_name,
        "sample_size": statistics["sample_size"],
        "mean": statistics["mean"],
        "standard_deviation": statistics["standard_deviation"],
        "status": "success",
    }

