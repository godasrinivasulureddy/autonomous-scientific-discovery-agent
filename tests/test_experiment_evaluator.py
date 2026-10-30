"""Tests for agents/experiment_evaluator.py (Day 5 integration)."""

import json

import pytest

from agents.experiment_evaluator import (
    evaluate_experiment_output,
    find_requests,
    infer_design,
)

TWO = {"label": "A vs B", "groups": {"A": [1, 2, 3, 4, 5], "B": [3, 4, 5, 6, 7]}}
PAIRED = {"label": "before/after", "paired": True,
          "groups": {"before": [10, 12, 14, 16, 18], "after": [11, 14, 15, 19, 20]}}


def test_stats_key_is_found_and_evaluated():
    out = evaluate_experiment_output({"success": True, "stats": [TWO]})
    assert out["status"] == "ok"
    assert out["results"][0]["design"] == "two_sample"
    assert out["results"][0]["p_value"] == pytest.approx(0.0805, abs=1e-4)
    assert out["summary"]["tests_run"] == 1


def test_numbers_printed_as_json_in_stdout():
    stdout = "training...\nepoch 3 done\n" + json.dumps({"stats": [TWO]})
    out = evaluate_experiment_output({"success": True, "stdout": stdout, "stderr": ""})
    assert out["status"] == "ok"


def test_numbers_inside_result_dict_and_json_string():
    assert evaluate_experiment_output({"result": {"statistics": TWO}})["status"] == "ok"
    assert evaluate_experiment_output({"result": json.dumps({"stats": [TWO]})})["status"] == "ok"


def test_output_given_as_json_text():
    assert evaluate_experiment_output(json.dumps({"stats": [TWO]}))["status"] == "ok"


def test_output_that_is_already_a_request():
    out = evaluate_experiment_output(dict(TWO, design="two_sample"))
    assert out["status"] == "ok"


@pytest.mark.parametrize("failed", [
    {"success": False, "error": "SyntaxError: bad code"},
    {"status": "timeout"},
    {"returncode": 1, "stderr": "Traceback..."},
    {"timed_out": True},
    {"error": "Docker container exited"},
])
def test_failed_experiments_are_not_analysed(failed):
    out = evaluate_experiment_output(dict(failed, stats=[TWO]))
    assert out["status"] == "experiment_failed"
    assert out["results"] == []
    assert "No statistical conclusion" in out["critique"]


def test_no_statistics_found():
    out = evaluate_experiment_output({"success": True, "stdout": "all done"})
    assert out["status"] == "no_statistics_found"
    assert "JSON" in out["reason"]


@pytest.mark.parametrize("bad", [None, 42, ["a", "b"]])
def test_invalid_output_types(bad):
    assert evaluate_experiment_output(bad)["status"] == "invalid_output"


def test_design_is_inferred():
    assert infer_design({"groups": {"a": [1], "b": [2]}})["design"] == "two_sample"
    assert infer_design({"groups": {"a": [1], "b": [2]}, "paired": True})["design"] == "paired"
    assert infer_design({"groups": {"a": [1], "b": [2], "c": [3]}})["design"] == "multi_group"
    assert infer_design({"groups": {"a": [1]}, "popmean": 0})["design"] == "one_sample"
    assert infer_design({"x": [1], "y": [2]})["design"] == "correlation"
    assert infer_design({"table": [[1, 2], [3, 4]]})["design"] == "contingency"
    assert infer_design({"design": "paired", "groups": {"a": [1]}})["design"] == "paired"


def test_paired_flag_is_used_end_to_end():
    out = evaluate_experiment_output({"stats": [PAIRED]})
    assert out["results"][0]["test_used"] == "Paired t-test"
    assert out["summary"]["may_claim_significance"] == ["before/after"]


def test_several_tests_get_holm_correction():
    out = evaluate_experiment_output({"stats": [TWO, PAIRED]})
    assert out["summary"]["tests_run"] == 2
    assert all(r["adjusted_p_value"] is not None for r in out["results"])


def test_bad_data_is_reported_not_raised():
    bad = {"label": "broken", "groups": {"A": [1, "x", 3], "B": [1, 2, 3]}}
    out = evaluate_experiment_output({"stats": [bad, TWO]})
    assert out["status"] == "ok"
    assert out["summary"]["counts"]["inconclusive"] == 1
    assert "broken" in out["critique"]


def test_unknown_design_when_it_cannot_be_inferred():
    out = evaluate_experiment_output({"stats": [{"label": "odd", "groups": {}}]})
    assert out["status"] == "ok"
    assert out["results"][0]["status"] in ("unsupported", "invalid_data")


def test_find_requests_returns_none_when_nothing_there():
    assert find_requests({"success": True}) is None


def test_whole_answer_is_json_serialisable():
    out = evaluate_experiment_output({"stats": [TWO, PAIRED]})
    assert json.loads(json.dumps(out))["status"] == "ok"
