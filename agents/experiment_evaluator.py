"""Connects experiment outputs to the Statistical Critic Agent (Week 3, Day 5).

The Code Executor returns a dict (or JSON text) for each experiment run. This
module finds the numbers inside it, runs the Statistical Critic on them, and
returns one structured answer the rest of the workflow can use.

How the experiment code should report its numbers
-------------------------------------------------
End the experiment script by printing ONE JSON object, for example:

    print(json.dumps({"stats": [{
        "label": "Model A vs B accuracy",
        "groups": {"model_a": [0.81, 0.83, 0.80], "model_b": [0.86, 0.88, 0.85]},
    }]}))

The "design" key is optional: it is worked out from the data
(two groups -> two_sample, three or more -> multi_group, x and y -> correlation,
table -> contingency, one group plus popmean -> one_sample). Add "paired": true
for matched measurements.

Where the numbers can be found (first match wins)
-------------------------------------------------
1. the output itself, if it already looks like a request ("design", "groups", ...)
2. output["stats"], ["statistics"], ["stat_tests"], ["tests"], ["stats_request"]
3. the same keys inside output["result"] or output["results"]
4. a JSON object printed in output["stdout"] (last JSON line wins)

If the experiment itself failed (success False, non-zero exit code, timeout or
an error message), no statistics are run and the answer says so.
"""

import json

from agents.statistical_critic import StatisticalCriticAgent

PAYLOAD_KEYS = ("stats", "statistics", "stat_tests", "tests", "stats_request")
REQUEST_HINTS = ("design", "groups", "x", "table")
FAILED_STATUS_WORDS = ("error", "failed", "failure", "timeout", "timed_out")


# ----------------------------------------------------------------------------
# Finding the numbers
# ----------------------------------------------------------------------------

def _failure_reason(output):
    """Return why the experiment failed, or None if it looks successful."""
    if output.get("success") is False:
        return str(output.get("error") or output.get("stderr") or "success flag is False").strip()[:300]
    status = str(output.get("status", "")).lower()
    if status in FAILED_STATUS_WORDS:
        return "status is %r" % status
    if output.get("timed_out") or output.get("timeout") is True:
        return "the experiment timed out"
    for key in ("returncode", "exit_code", "return_code"):
        code = output.get(key)
        if isinstance(code, int) and not isinstance(code, bool) and code != 0:
            return "exit code %d" % code
    error = output.get("error")
    if error:
        return str(error).strip()[:300]
    return None


def _json_from_text(text):
    """Parse JSON from text. Falls back to the last line that is valid JSON."""
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        return json.loads(text)
    except ValueError:
        pass
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line[:1] in ("{", "["):
            try:
                return json.loads(line)
            except ValueError:
                continue
    return None


def _as_requests(value):
    """Turn a dict or list of dicts into a list of request dicts, else None."""
    if isinstance(value, str):
        value = _json_from_text(value)
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and value and all(isinstance(v, dict) for v in value):
        return value
    return None


def _looks_like_request(d):
    return isinstance(d, dict) and any(k in d for k in REQUEST_HINTS)


def _search(container):
    """Look for requests directly in a dict. Returns a list or None."""
    if not isinstance(container, dict):
        return None
    if _looks_like_request(container):
        return [container]
    for key in PAYLOAD_KEYS:
        if key in container:
            found = _as_requests(container[key])
            if found:
                return found
    return None


def find_requests(output):
    """Locate statistical requests inside an experiment output."""
    found = _search(output)
    if found:
        return found
    for key in ("result", "results", "output", "data"):
        inner = output.get(key)
        if isinstance(inner, str):
            inner = _json_from_text(inner)
        if isinstance(inner, list):
            as_list = _as_requests(inner)
            if as_list and all(_looks_like_request(r) for r in as_list):
                return as_list
        found = _search(inner)
        if found:
            return found
    printed = _json_from_text(output.get("stdout"))
    if isinstance(printed, list):
        as_list = _as_requests(printed)
        if as_list and all(_looks_like_request(r) for r in as_list):
            return as_list
    return _search(printed)


def infer_design(request):
    """Add a 'design' to a request that lacks one. Returns a new dict."""
    req = dict(request)
    if req.get("design"):
        return req
    groups = req.get("groups")
    if "table" in req:
        req["design"] = "contingency"
    elif "x" in req and "y" in req:
        req["design"] = "correlation"
    elif isinstance(groups, dict):
        n = len(groups)
        if n == 1:
            req["design"] = "one_sample"
        elif n == 2:
            req["design"] = "paired" if req.get("paired") else "two_sample"
        elif n >= 3:
            req["design"] = "multi_group"
    return req


# ----------------------------------------------------------------------------
# Public function
# ----------------------------------------------------------------------------

def evaluate_experiment_output(output, agent=None):
    """Statistically evaluate one experiment output.

    Returns a dict:
      status    ok | experiment_failed | no_statistics_found | invalid_output
      reason    short text when status is not ok
      results   list of StatResult dicts (empty unless status is ok)
      critique  text block for the hypothesis / experiment agents
      summary   counts, and which labels may claim significance
    """
    agent = agent or StatisticalCriticAgent()

    if isinstance(output, str):
        output = _json_from_text(output) or {"stdout": output}
    if not isinstance(output, dict):
        return _answer("invalid_output", "The experiment output must be a dict or JSON text.")

    reason = _failure_reason(output)
    if reason:
        return _answer("experiment_failed",
                       "The experiment did not run successfully (%s), so no statistics were run." % reason)

    requests = find_requests(output)
    if not requests:
        return _answer("no_statistics_found",
                       "No statistics payload was found. The experiment should print a JSON object "
                       "with a 'stats' list (see agents/experiment_evaluator.py).")

    requests = [infer_design(r) for r in requests]
    results = agent.evaluate_many(requests)

    claims = []
    for r in results:
        if agent.check_claim(r, "significant")["allowed"]:
            claims.append(r.label or r.design)
    counts = {"significant": 0, "not_significant": 0, "inconclusive": 0}
    for r in results:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1

    return {
        "status": "ok",
        "reason": "",
        "results": [r.to_dict() for r in results],
        "critique": agent.critique(results),
        "summary": {"tests_run": len(results), "counts": counts, "may_claim_significance": claims},
    }


def _answer(status, reason):
    return {
        "status": status,
        "reason": reason,
        "results": [],
        "critique": "No statistical conclusion: " + reason,
        "summary": {"tests_run": 0, "counts": {"significant": 0, "not_significant": 0, "inconclusive": 0},
                    "may_claim_significance": []},
    }
