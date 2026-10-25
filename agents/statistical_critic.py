"""Statistical Critic Agent interface and evaluation utilities.

Evaluates experiment results and hypotheses, checking statistical significance,
assumptions, confidence intervals, and p-values according to scientific standards.
"""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


def evaluate_experiment_results(
    hypothesis: str,
    experiment_result: dict[str, Any],
    alpha: float = 0.05,
    test_type: str = "descriptive",
) -> dict[str, Any]:
    """Evaluate experiment outputs against scientific and statistical criteria.

    Args:
        hypothesis: Research hypothesis string being tested.
        experiment_result: Output dictionary from code_executor.
        alpha: Significance threshold (default 0.05).
        test_type: Type of statistical test ("descriptive", "t_test", etc.).

    Returns:
        Structured evaluation dict conforming to Week 3 architecture spec.
    """
    if not isinstance(hypothesis, str) or not hypothesis.strip():
        raise ValueError("Hypothesis must be a non-empty string.")

    if not isinstance(experiment_result, dict):
        raise ValueError("experiment_result must be a dictionary.")

    if not (0 < alpha < 1):
        raise ValueError("alpha must be between 0 and 1 exclusive.")

    status = experiment_result.get("status")

    # Handle skipped or incomplete experiment results
    if status == "skipped":
        return {
            "status": "inconclusive",
            "test_name": test_type,
            "p_value": None,
            "confidence_interval": None,
            "significant": False,
            "assumptions_met": False,
            "criticism": f"Experiment was skipped: {experiment_result.get('reason', 'No experiment executed.')}",
            "recommendations": ["Provide valid numerical experiment values to evaluate hypothesis."],
        }

    # Handle errors during execution
    if status != "success":
        err_msg = experiment_result.get("error", "Unknown execution error.")
        return {
            "status": "failed",
            "test_name": test_type,
            "p_value": None,
            "confidence_interval": None,
            "significant": False,
            "assumptions_met": False,
            "criticism": f"Experiment failed during execution: {err_msg}",
            "recommendations": ["Debug execution code or fix runtime parameters."],
        }

    sample_size = experiment_result.get("sample_size")
    mean_val = experiment_result.get("mean")
    std_val = experiment_result.get("standard_deviation")

    if sample_size is None or mean_val is None or std_val is None:
        return {
            "status": "inconclusive",
            "test_name": test_type,
            "p_value": None,
            "confidence_interval": None,
            "significant": False,
            "assumptions_met": False,
            "criticism": "Experiment result is missing required statistical parameters (sample_size, mean, standard_deviation).",
            "recommendations": ["Ensure experiment outputs include standard descriptive metrics."],
        }

    if sample_size < 2:
        return {
            "status": "inconclusive",
            "test_name": test_type,
            "p_value": None,
            "confidence_interval": None,
            "significant": False,
            "assumptions_met": False,
            "criticism": f"Insufficient sample size (n={sample_size}) for robust statistical inference.",
            "recommendations": ["Increase sample size to at least n >= 3, preferably n >= 30."],
        }

    # Calculate 95% Confidence Interval for the mean using normal approximation / t-approx
    # Margin of error approx: 1.96 * (std / sqrt(n)) for n >= 30, or conservative 2.0+ for smaller n
    t_critical = 1.96 if sample_size >= 30 else 2.262  # approx t(df=9, 0.05) fallback
    standard_error = std_val / math.sqrt(sample_size)
    margin_of_error = t_critical * standard_error

    ci_lower = round(mean_val - margin_of_error, 4)
    ci_upper = round(mean_val + margin_of_error, 4)

    # In single-sample descriptive contexts: check if standard deviation is valid and non-zero
    is_variance_positive = std_val > 0
    assumptions_met = sample_size >= 2 and is_variance_positive

    # Check whether the confidence interval excludes zero or meets significance
    excludes_zero = not (ci_lower <= 0 <= ci_upper)

    recommendations: list[str] = []
    if sample_size < 10:
        recommendations.append("Consider collecting more replicates to increase statistical power.")
    if std_val == 0:
        recommendations.append("Identical values observed (std=0); check data source for lack of variance.")

    criticism = (
        f"Sample size n={sample_size}, Mean={mean_val:.4f}, StdDev={std_val:.4f}. "
        f"95% CI is [{ci_lower}, {ci_upper}]."
    )

    return {
        "status": "evaluated",
        "test_name": test_type,
        "p_value": None,  # Descriptive test has no null hypothesis p-value
        "confidence_interval": [ci_lower, ci_upper],
        "significant": excludes_zero,
        "assumptions_met": assumptions_met,
        "criticism": criticism,
        "recommendations": recommendations,
    }
