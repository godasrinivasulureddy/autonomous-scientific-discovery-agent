
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
