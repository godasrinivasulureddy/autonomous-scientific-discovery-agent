from __future__ import annotations
"""Statistical Critic Agent (Week 3, Member 2).

Takes the numbers produced by an experiment, picks a suitable statistical test,
runs it with SciPy, and returns a structured, explained result.

Supported designs
-----------------
two_sample   two independent groups      Welch t-test / Mann-Whitney U
paired       two matched measurements    paired t-test / Wilcoxon signed-rank
one_sample   one group vs a known value  one-sample t-test / Wilcoxon signed-rank
multi_group  three or more groups        one-way ANOVA / Kruskal-Wallis
correlation  two numeric variables       Pearson / Spearman
contingency  table of counts             chi-square / Fisher exact (2x2, small counts)

Request format (a plain dict)
-----------------------------
{
  "design": "two_sample",
  "groups": {"control": [..], "treatment": [..]},   # not for correlation/contingency
  "method": "auto",          # "auto" | "parametric" | "nonparametric"  (optional)
  "alpha": 0.05,             # optional
  "popmean": 0.0,            # one_sample only
  "x": [..], "y": [..],      # correlation only
  "table": [[..], [..]],     # contingency only
  "label": "accuracy of model A vs B",   # optional, shown in explanations
}

The agent never raises on bad data. It returns a StatResult whose status says
what went wrong, and whose verdict stays "inconclusive".
"""

import math
from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np
from scipy import stats

DEFAULT_ALPHA = 0.05
MIN_N = 3                 # fewer values than this per group: no test is run
LOW_N = 8                 # fewer than this: results are flagged as preliminary
LARGE_N = 30              # at or above this, t-tests are fine even if not normal
BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 12345    # fixed, so results are repeatable

SUPPORTED_DESIGNS = (
    "two_sample", "paired", "one_sample", "multi_group", "correlation", "contingency",
)


# ----------------------------------------------------------------------------
# Result object
# ----------------------------------------------------------------------------

@dataclass
class StatResult:
    status: str = "ok"      # ok | invalid_data | insufficient_data | unsupported | error
    design: str = ""
    test_used: str = ""
    statistic: Optional[float] = None
    p_value: Optional[float] = None
    adjusted_p_value: Optional[float] = None   # filled by evaluate_many (Holm)
    alpha: float = DEFAULT_ALPHA
    verdict: str = "inconclusive"   # significant | not_significant | inconclusive
    effect_size: dict = field(default_factory=dict)
    confidence_interval: dict = field(default_factory=dict)
    sample_sizes: dict = field(default_factory=dict)
    assumptions: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    limitations: list = field(default_factory=list)
    explanation: str = ""
    label: str = ""

    def to_dict(self):
        return asdict(self)


class DataError(Exception):
    """The data cannot be analysed (wrong type, no variation, bad shape...)."""


class InsufficientDataError(Exception):
    """Too few values to run the test."""


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def _f(x):
    """Plain float (JSON friendly) or None."""
    if x is None:
        return None
    x = float(x)
    return x if math.isfinite(x) else None


def _clean(values, name, warnings):
    """Turn a list into a float array. Drops None/NaN, rejects text and inf."""
    if values is None:
        raise DataError("'%s' is missing." % name)
    try:
        items = list(values)
    except TypeError:
        raise DataError("'%s' must be a list of numbers." % name)
    cleaned, dropped = [], 0
    for v in items:
        if v is None:
            dropped += 1
            continue
        try:
            number = float(v)
        except (TypeError, ValueError):
            raise DataError("'%s' contains a non-numeric value: %r." % (name, v))
        if math.isnan(number):
            dropped += 1
        elif math.isinf(number):
            raise DataError("'%s' contains an infinite value." % name)
        else:
            cleaned.append(number)
    if dropped:
        warnings.append("Dropped %d missing value(s) from '%s'." % (dropped, name))
    return np.array(cleaned, dtype=float)


def _need(arr, name, minimum=MIN_N):
    if len(arr) < minimum:
        raise InsufficientDataError(
            "'%s' has %d usable value(s); at least %d are needed." % (name, len(arr), minimum))


def _need_variation(*arrays):
    if all(np.ptp(a) == 0 for a in arrays):
        raise DataError("All values are identical, so there is no variation to test.")


def _normality(arr, label):
    """Shapiro-Wilk check. passed is None when the check cannot be run."""
    name = "Normality of %s (Shapiro-Wilk)" % label
    if len(arr) < 3 or np.ptp(arr) == 0:
        return {"name": name, "passed": None, "detail": "not enough variation to check"}
    sample = arr
    if len(arr) > 5000:   # Shapiro-Wilk is only reliable up to 5000 values
        sample = arr[np.linspace(0, len(arr) - 1, 5000).astype(int)]
    p = float(stats.shapiro(sample).pvalue)
    return {"name": name, "passed": bool(p > 0.05), "detail": "p = %.4f" % p}


def _any_failed(checks):
    return any(c["passed"] is False for c in checks)


def _choose_parametric(method, checks, smallest_n):
    """Decide parametric vs non-parametric. Returns (use_parametric, note)."""
    failed = _any_failed(checks)
    if method == "parametric":
        note = "Parametric test forced, but an assumption check failed." if failed else None
        return True, note
    if method == "nonparametric":
        return False, None
    # auto
    if failed and smallest_n < LARGE_N:
        return False, "Assumption check failed with a small sample, so a rank-based test was used."
    return True, None


def _magnitude(value, kind):
    """Plain-language size of an effect (Cohen-style cut-offs)."""
    cuts = {"d": (0.2, 0.5, 0.8), "r": (0.1, 0.3, 0.5),
            "eta2": (0.01, 0.06, 0.14), "v": (0.1, 0.3, 0.5)}[kind]
    v = abs(value)
    if v < cuts[0]:
        return "negligible"
    if v < cuts[1]:
        return "small"
    if v < cuts[2]:
        return "medium"
    return "large"


def _set_effect(res, name, value, kind):
    value = _f(value)
    if value is None:
        return
    res.effect_size = {"name": name, "value": round(value, 4), "magnitude": _magnitude(value, kind)}


def _set_ci(res, what, low, high, level, method):
    low, high = _f(low), _f(high)
    if low is None or high is None:
        return
    res.confidence_interval = {
        "what": what, "level": round(level, 4),
        "low": round(low, 4), "high": round(high, 4), "method": method,
    }


def _bootstrap_ci(arrays, stat_fn, alpha):
    """Percentile bootstrap CI. Each array is resampled independently."""
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    reps = np.empty(BOOTSTRAP_RESAMPLES)
    for i in range(BOOTSTRAP_RESAMPLES):
        sample = [rng.choice(a, size=len(a), replace=True) for a in arrays]
        reps[i] = stat_fn(*sample)
    return (float(np.percentile(reps, 100 * alpha / 2)),
            float(np.percentile(reps, 100 * (1 - alpha / 2))))


def _t_interval(mean, se, df, alpha):
    crit = stats.t.ppf(1 - alpha / 2, df)
    return mean - crit * se, mean + crit * se


# ----------------------------------------------------------------------------
# One function per design
# ----------------------------------------------------------------------------

def _two_sample(req, res, alpha):
    groups = req.get("groups") or {}
    if len(groups) != 2:
        raise DataError("two_sample needs exactly 2 groups in 'groups'.")
    (na_name, a_raw), (nb_name, b_raw) = list(groups.items())
    a = _clean(a_raw, na_name, res.warnings)
    b = _clean(b_raw, nb_name, res.warnings)
    _need(a, na_name)
    _need(b, nb_name)
    _need_variation(a, b)
    res.sample_sizes = {na_name: len(a), nb_name: len(b)}

    checks = [_normality(a, na_name), _normality(b, nb_name)]
    if np.ptp(a) > 0 and np.ptp(b) > 0:
        lev = float(stats.levene(a, b).pvalue)
        checks.append({"name": "Equal variances (Levene)", "passed": bool(lev > 0.05),
                       "detail": "p = %.4f (Welch's test does not need this)" % lev})
    res.assumptions = checks
    parametric, note = _choose_parametric(req.get("method", "auto"), checks[:2], min(len(a), len(b)))
    if note:
        res.warnings.append(note)

    diff = float(a.mean() - b.mean())
    level = 1 - alpha
    if parametric:
        res.test_used = "Welch two-sample t-test"
        t = stats.ttest_ind(a, b, equal_var=False)
        res.statistic, res.p_value = _f(t.statistic), _f(t.pvalue)
        va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
        se = math.sqrt(va + vb)
        df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
        lo, hi = _t_interval(diff, se, df, alpha)
        _set_ci(res, "mean(%s) - mean(%s)" % (na_name, nb_name), lo, hi, level, "Welch t interval")
        sp = math.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1))
                       / (len(a) + len(b) - 2))
        _set_effect(res, "Cohen's d", diff / sp if sp > 0 else None, "d")
    else:
        res.test_used = "Mann-Whitney U test"
        u = stats.mannwhitneyu(a, b, alternative="two-sided")
        res.statistic, res.p_value = _f(u.statistic), _f(u.pvalue)
        lo, hi = _bootstrap_ci([a, b], lambda x, y: np.median(x) - np.median(y), alpha)
        _set_ci(res, "median(%s) - median(%s)" % (na_name, nb_name), lo, hi, level,
                "bootstrap (%d resamples)" % BOOTSTRAP_RESAMPLES)
        _set_effect(res, "rank-biserial r", 2 * u.statistic / (len(a) * len(b)) - 1, "r")
        if len(a) + len(b) < 20 and (np.unique(np.concatenate([a, b])).size < len(a) + len(b)):
            res.warnings.append("Tied values present; the p-value is approximate.")

    higher = na_name if diff > 0 else nb_name
    what = "%s vs %s" % (na_name, nb_name)
    if diff == 0:
        direction = "The group means are identical."
    else:
        direction = "%s has the higher mean (difference %.4g)." % (higher, abs(diff))
    return what, direction


def _paired(req, res, alpha):
    groups = req.get("groups") or {}
    if len(groups) != 2:
        raise DataError("paired needs exactly 2 groups (the two matched measurements).")
    (na_name, a_raw), (nb_name, b_raw) = list(groups.items())
    a_list, b_list = list(a_raw or []), list(b_raw or [])
    if len(a_list) != len(b_list):
        raise DataError("Paired groups must have the same length (%d vs %d)." % (len(a_list), len(b_list)))
    keep_a, keep_b, dropped = [], [], 0
    for x, y in zip(a_list, b_list):
        try:
            fx = None if x is None else float(x)
            fy = None if y is None else float(y)
        except (TypeError, ValueError):
            raise DataError("Paired data contains a non-numeric value.")
        if fx is None or fy is None or math.isnan(fx) or math.isnan(fy):
            dropped += 1
        elif math.isinf(fx) or math.isinf(fy):
            raise DataError("Paired data contains an infinite value.")
        else:
            keep_a.append(fx)
            keep_b.append(fy)
    if dropped:
        res.warnings.append("Dropped %d incomplete pair(s)." % dropped)
    a, b = np.array(keep_a), np.array(keep_b)
    d = a - b
    _need(d, "paired differences")
    _need_variation(d)
    res.sample_sizes = {"pairs": len(d)}

    checks = [_normality(d, "the paired differences")]
    res.assumptions = checks
    parametric, note = _choose_parametric(req.get("method", "auto"), checks, len(d))
    if note:
        res.warnings.append(note)

    level = 1 - alpha
    mean_d = float(d.mean())
    if parametric:
        res.test_used = "Paired t-test"
        t = stats.ttest_rel(a, b)
        res.statistic, res.p_value = _f(t.statistic), _f(t.pvalue)
        se = float(d.std(ddof=1) / math.sqrt(len(d)))
        lo, hi = _t_interval(mean_d, se, len(d) - 1, alpha)
        _set_ci(res, "mean(%s - %s)" % (na_name, nb_name), lo, hi, level, "t interval")
        sd = float(d.std(ddof=1))
        _set_effect(res, "Cohen's d (paired)", mean_d / sd if sd > 0 else None, "d")
    else:
        res.test_used = "Wilcoxon signed-rank test"
        nonzero = d[d != 0]
        if len(nonzero) < MIN_N:
            raise InsufficientDataError("Fewer than %d non-zero paired differences." % MIN_N)
        w = stats.wilcoxon(nonzero)
        res.statistic, res.p_value = _f(w.statistic), _f(w.pvalue)
        lo, hi = _bootstrap_ci([d], lambda x: np.median(x), alpha)
        _set_ci(res, "median(%s - %s)" % (na_name, nb_name), lo, hi, level,
                "bootstrap (%d resamples)" % BOOTSTRAP_RESAMPLES)
        ranks = stats.rankdata(np.abs(nonzero))
        w_plus, w_minus = ranks[nonzero > 0].sum(), ranks[nonzero < 0].sum()
        _set_effect(res, "matched-pairs rank-biserial r", (w_plus - w_minus) / (w_plus + w_minus), "r")

    what = "%s vs %s (paired)" % (na_name, nb_name)
    if mean_d == 0:
        direction = "The mean paired difference is zero."
    else:
        direction = "%s is %s %s on average (mean difference %.4g)." % (
            na_name, "higher than" if mean_d > 0 else "lower than", nb_name, abs(mean_d))
    return what, direction


def _one_sample(req, res, alpha):
    groups = req.get("groups") or {}
    if len(groups) != 1:
        raise DataError("one_sample needs exactly 1 group in 'groups'.")
    if "popmean" not in req:
        raise DataError("one_sample needs 'popmean' (the value to compare against).")
    try:
        popmean = float(req["popmean"])
    except (TypeError, ValueError):
        raise DataError("'popmean' must be a number.")
    name, raw = list(groups.items())[0]
    x = _clean(raw, name, res.warnings)
    _need(x, name)
    _need_variation(x)
    res.sample_sizes = {name: len(x)}

    checks = [_normality(x, name)]
    res.assumptions = checks
    parametric, note = _choose_parametric(req.get("method", "auto"), checks, len(x))
    if note:
        res.warnings.append(note)

    level = 1 - alpha
    mean = float(x.mean())
    if parametric:
        res.test_used = "One-sample t-test"
        t = stats.ttest_1samp(x, popmean)
        res.statistic, res.p_value = _f(t.statistic), _f(t.pvalue)
        se = float(x.std(ddof=1) / math.sqrt(len(x)))
        lo, hi = _t_interval(mean, se, len(x) - 1, alpha)
        _set_ci(res, "mean of %s" % name, lo, hi, level, "t interval")
        sd = float(x.std(ddof=1))
        _set_effect(res, "Cohen's d", (mean - popmean) / sd if sd > 0 else None, "d")
    else:
        res.test_used = "Wilcoxon signed-rank test (one sample)"
        diffs = x - popmean
        nonzero = diffs[diffs != 0]
        if len(nonzero) < MIN_N:
            raise InsufficientDataError("Fewer than %d values differ from %g." % (MIN_N, popmean))
        w = stats.wilcoxon(nonzero)
        res.statistic, res.p_value = _f(w.statistic), _f(w.pvalue)
        lo, hi = _bootstrap_ci([x], lambda v: np.median(v), alpha)
        _set_ci(res, "median of %s" % name, lo, hi, level, "bootstrap (%d resamples)" % BOOTSTRAP_RESAMPLES)
        ranks = stats.rankdata(np.abs(nonzero))
        w_plus, w_minus = ranks[nonzero > 0].sum(), ranks[nonzero < 0].sum()
        _set_effect(res, "matched-pairs rank-biserial r", (w_plus - w_minus) / (w_plus + w_minus), "r")

    what = "%s vs the reference value %g" % (name, popmean)
    if mean == popmean:
        direction = "The sample mean equals the reference value."
    else:
        direction = "The sample mean (%.4g) is %s the reference value." % (
            mean, "above" if mean > popmean else "below")
    return what, direction


def _multi_group(req, res, alpha):
    groups = req.get("groups") or {}
    if len(groups) < 3:
        raise DataError("multi_group needs at least 3 groups (use two_sample for 2).")
    arrays, names = [], []
    for name, raw in groups.items():
        arr = _clean(raw, name, res.warnings)
        _need(arr, name)
        arrays.append(arr)
        names.append(name)
    _need_variation(*arrays)
    res.sample_sizes = {n: len(a) for n, a in zip(names, arrays)}

    checks = [_normality(a, n) for n, a in zip(names, arrays)]
    if all(np.ptp(a) > 0 for a in arrays):
        lev = float(stats.levene(*arrays).pvalue)
        checks.append({"name": "Equal variances (Levene)", "passed": bool(lev > 0.05),
                       "detail": "p = %.4f" % lev})
    res.assumptions = checks
    parametric, note = _choose_parametric(req.get("method", "auto"), checks,
                                          min(len(a) for a in arrays))
    if note:
        res.warnings.append(note)

    all_values = np.concatenate(arrays)
    n_total, k = len(all_values), len(arrays)
    if parametric:
        res.test_used = "One-way ANOVA"
        f = stats.f_oneway(*arrays)
        res.statistic, res.p_value = _f(f.statistic), _f(f.pvalue)
        grand = all_values.mean()
        ss_between = sum(len(a) * (a.mean() - grand) ** 2 for a in arrays)
        ss_total = float(((all_values - grand) ** 2).sum())
        _set_effect(res, "eta squared", ss_between / ss_total if ss_total > 0 else None, "eta2")
    else:
        res.test_used = "Kruskal-Wallis H test"
        h = stats.kruskal(*arrays)
        res.statistic, res.p_value = _f(h.statistic), _f(h.pvalue)
        _set_effect(res, "epsilon squared", float(h.statistic) / (n_total - 1), "eta2")

    res.limitations.append(
        "The omnibus test only says that at least one group differs. "
        "Run corrected pairwise follow-up tests to find which ones.")
    return "%d groups (%s)" % (k, ", ".join(names)), ""


def _correlation(req, res, alpha):
    if "x" not in req or "y" not in req:
        raise DataError("correlation needs 'x' and 'y'.")
    x_list, y_list = list(req["x"] or []), list(req["y"] or [])
    if len(x_list) != len(y_list):
        raise DataError("'x' and 'y' must have the same length (%d vs %d)." % (len(x_list), len(y_list)))
    keep_x, keep_y, dropped = [], [], 0
    for a, b in zip(x_list, y_list):
        try:
            fa = None if a is None else float(a)
            fb = None if b is None else float(b)
        except (TypeError, ValueError):
            raise DataError("Correlation data contains a non-numeric value.")
        if fa is None or fb is None or math.isnan(fa) or math.isnan(fb):
            dropped += 1
        elif math.isinf(fa) or math.isinf(fb):
            raise DataError("Correlation data contains an infinite value.")
        else:
            keep_x.append(fa)
            keep_y.append(fb)
    if dropped:
        res.warnings.append("Dropped %d incomplete pair(s)." % dropped)
    x, y = np.array(keep_x), np.array(keep_y)
    _need(x, "x/y pairs", minimum=4)
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        raise DataError("x or y is constant, so a correlation is undefined.")
    res.sample_sizes = {"pairs": len(x)}

    checks = [_normality(x, "x"), _normality(y, "y")]
    res.assumptions = checks
    parametric, note = _choose_parametric(req.get("method", "auto"), checks, len(x))
    if note:
        res.warnings.append(note)

    if parametric:
        res.test_used = "Pearson correlation"
        out = stats.pearsonr(x, y)
        r, se_factor = float(out.statistic), 1.0
    else:
        res.test_used = "Spearman rank correlation"
        out = stats.spearmanr(x, y)
        r, se_factor = float(out.statistic), 1.06   # Fieller et al. adjustment
    res.statistic, res.p_value = _f(r), _f(out.pvalue)
    _set_effect(res, "r", r, "r")
    if abs(r) < 1 and len(x) > 3:
        z = math.atanh(r)
        se = math.sqrt(se_factor / (len(x) - 3))
        crit = stats.norm.ppf(1 - alpha / 2)
        _set_ci(res, "correlation coefficient", math.tanh(z - crit * se), math.tanh(z + crit * se),
                1 - alpha, "Fisher z transform")
    res.limitations.append("Correlation does not show causation.")
    direction = "The relationship is %s (r = %.3f)." % ("positive" if r > 0 else "negative", r)
    return "x vs y", direction


def _contingency(req, res, alpha):
    table = req.get("table")
    try:
        arr = np.array(table, dtype=float)
    except (TypeError, ValueError):
        raise DataError("'table' must be a grid of counts.")
    if arr.ndim != 2 or arr.shape[0] < 2 or arr.shape[1] < 2:
        raise DataError("'table' must be at least 2 rows by 2 columns.")
    if not np.all(np.isfinite(arr)) or (arr < 0).any():
        raise DataError("'table' must contain only non-negative, finite counts.")
    if (arr != np.round(arr)).any():
        raise DataError("'table' must contain whole-number counts.")
    if (arr.sum(axis=0) == 0).any() or (arr.sum(axis=1) == 0).any():
        raise DataError("A row or column of 'table' sums to zero.")
    n = float(arr.sum())
    if n < 5:
        raise InsufficientDataError("The table has only %d observations." % n)
    res.sample_sizes = {"observations": int(n)}

    chi2, p, dof, expected = stats.chi2_contingency(arr, correction=False)
    small = float((expected < 5).mean())
    res.assumptions = [{
        "name": "Expected counts at least 5",
        "passed": bool(small == 0),
        "detail": "%.0f%% of cells have an expected count below 5" % (100 * small),
    }]
    v = math.sqrt(chi2 / (n * (min(arr.shape) - 1)))
    is_2x2 = arr.shape == (2, 2)
    method = req.get("method", "auto")
    use_fisher = is_2x2 and (method == "nonparametric" or (method == "auto" and small > 0))
    if use_fisher:
        res.test_used = "Fisher exact test"
        odds, p_val = stats.fisher_exact(arr)
        res.statistic, res.p_value = _f(odds), _f(p_val)
        res.warnings.append("Statistic shown is the odds ratio.")
    else:
        res.test_used = "Chi-square test of independence"
        if is_2x2:
            c = stats.chi2_contingency(arr, correction=True)
            res.statistic, res.p_value = _f(c[0]), _f(c[1])
            res.test_used += " (Yates correction)"
        else:
            res.statistic, res.p_value = _f(chi2), _f(p)
        if small > 0:
            res.warnings.append(
                "Some expected counts are below 5; the chi-square approximation may be unreliable.")
    _set_effect(res, "Cramer's V", v, "v")
    res.limitations.append("An association in a table does not show causation.")
    return "the row and column categories", ""


DESIGNS = {
    "two_sample": _two_sample,
    "paired": _paired,
    "one_sample": _one_sample,
    "multi_group": _multi_group,
    "correlation": _correlation,
    "contingency": _contingency,
}


# ----------------------------------------------------------------------------
# Verdict and explanation
# ----------------------------------------------------------------------------

def _finish(res, what, direction):
    """Set the verdict, add caveats, and write the plain-language explanation."""
    if res.p_value is None:
        res.verdict = "inconclusive"
        res.explanation = "The test did not produce a p-value, so no conclusion can be drawn."
        return
    significant = res.p_value < res.alpha
    res.verdict = "significant" if significant else "not_significant"

    n_values = [v for v in res.sample_sizes.values()]
    smallest = min(n_values) if n_values else None
    if res.design != "contingency" and smallest is not None and smallest < LOW_N:
        res.limitations.append(
            "Small sample (smallest group has %d values): low power and unstable estimates. "
            "Treat this result as preliminary." % smallest)
    if res.design == "contingency" and smallest is not None and smallest < 20:
        res.limitations.append("Very few observations; treat this result as preliminary.")
    if significant and res.effect_size.get("magnitude") == "negligible":
        res.warnings.append("Statistically significant, but the effect size is negligible.")
    if _any_failed(res.assumptions) and res.test_used in (
            "Welch two-sample t-test", "Paired t-test", "One-sample t-test",
            "One-way ANOVA", "Pearson correlation"):
        res.warnings.append("A normality check failed; interpret the p-value with caution.")
    res.limitations.append(
        "A p-value is not the probability that the hypothesis is true, "
        "and p below alpha does not guarantee the effect is real or important.")

    p_text = "p < 0.0001" if res.p_value < 0.0001 else "p = %.4f" % res.p_value
    parts = ["%s on %s gave statistic = %s, %s." % (
        res.test_used, what, "%.4g" % res.statistic if res.statistic is not None else "n/a", p_text)]
    if significant:
        parts.append("Because p is below alpha (%g), the result is statistically significant." % res.alpha)
    else:
        parts.append("Because p is not below alpha (%g), the result is NOT statistically significant: "
                     "the data do not rule out chance. This does not prove there is no effect." % res.alpha)
    if direction:
        parts.append(direction)
    if res.effect_size:
        parts.append("Effect size: %s = %s (%s)." % (
            res.effect_size["name"], res.effect_size["value"], res.effect_size["magnitude"]))
    if res.confidence_interval:
        ci = res.confidence_interval
        parts.append("%g%% confidence interval for %s: [%s, %s] (%s)." % (
            round(ci["level"] * 100, 4), ci["what"], ci["low"], ci["high"], ci["method"]))
    res.explanation = " ".join(parts)


# ----------------------------------------------------------------------------
# The agent
# ----------------------------------------------------------------------------

def _fmt_p(p):
    return "< 0.0001" if p < 0.0001 else "= %.4f" % p


def holm_adjust(p_values):
    """Holm-Bonferroni correction. None entries stay None."""
    indexed = [(i, p) for i, p in enumerate(p_values) if p is not None]
    indexed.sort(key=lambda t: t[1])
    m = len(indexed)
    adjusted = [None] * len(p_values)
    running = 0.0
    for rank, (i, p) in enumerate(indexed):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[i] = running
    return adjusted


class StatisticalCriticAgent:
    """Evaluates experiment results statistically. Never raises on bad input."""

    def __init__(self, alpha=DEFAULT_ALPHA):
        if not (0 < alpha < 1):
            raise ValueError("alpha must be between 0 and 1.")
        self.alpha = alpha

    def evaluate(self, request):
        res = StatResult(alpha=self.alpha)
        try:
            if not isinstance(request, dict):
                raise DataError("The request must be a dict.")
            res.label = str(request.get("label", ""))
            res.design = str(request.get("design", ""))
            if "alpha" in request:
                try:
                    alpha = float(request["alpha"])
                except (TypeError, ValueError):
                    raise DataError("'alpha' must be a number.")
                if not (0 < alpha < 1):
                    raise DataError("'alpha' must be between 0 and 1.")
                res.alpha = alpha
            if res.design not in DESIGNS:
                res.status = "unsupported"
                res.explanation = "No conclusion: design %r is not supported. Supported: %s." % (
                    res.design, ", ".join(SUPPORTED_DESIGNS))
                return res
            if request.get("method", "auto") not in ("auto", "parametric", "nonparametric"):
                raise DataError("'method' must be auto, parametric or nonparametric.")
            what, direction = DESIGNS[res.design](request, res, res.alpha)
            _finish(res, what, direction)
        except InsufficientDataError as e:
            res.status = "insufficient_data"
            res.verdict = "inconclusive"
            res.explanation = "No conclusion can be drawn: %s" % e
        except DataError as e:
            res.status = "invalid_data"
            res.verdict = "inconclusive"
            res.explanation = "No conclusion can be drawn: %s" % e
        except Exception as e:   # fail safely: the workflow must keep running
            res.status = "error"
            res.verdict = "inconclusive"
            res.explanation = "No conclusion can be drawn: unexpected error (%s: %s)." % (
                type(e).__name__, e)
        return res

    def evaluate_many(self, requests):
        """Evaluate several tests and add Holm-adjusted p-values (multiple testing)."""
        results = [self.evaluate(r) for r in requests]
        usable = [r for r in results if r.status == "ok"]
        if len(usable) > 1:
            adjusted = holm_adjust([r.p_value for r in usable])
            for r, adj in zip(usable, adjusted):
                r.adjusted_p_value = _f(adj)
                survives = adj < r.alpha
                if (r.p_value < r.alpha) and not survives:
                    r.verdict = "not_significant"
                    r.warnings.append(
                        "Significant on its own (p = %.4f) but NOT after Holm correction for %d tests "
                        "(adjusted p = %.4f)." % (r.p_value, len(usable), adj))
                    r.explanation += (" After correcting for %d tests (Holm), the adjusted p-value is "
                                      "%.4f, so this is NOT significant." % (len(usable), adj))
                else:
                    r.explanation += (" Holm-adjusted p-value for %d tests: p %s." % (len(usable), _fmt_p(adj)))
        return results

    def check_claim(self, result, claim):
        """Guard against over-claiming. claim: 'significant' or 'no_difference'."""
        if claim == "significant":
            if result.status != "ok":
                return {"allowed": False, "reason": "The test could not be run: " + result.explanation}
            if result.verdict != "significant":
                return {"allowed": False,
                        "reason": "p = %.4f is not below alpha = %g, so significance cannot be claimed."
                                  % (result.p_value, result.alpha)}
            return {"allowed": True, "reason": "p = %.4f is below alpha = %g." % (
                result.p_value, result.alpha)}
        if claim == "no_difference":
            return {"allowed": False,
                    "reason": "A non-significant result is not evidence of no difference. "
                              "That needs an equivalence test or a very narrow confidence interval."}
        return {"allowed": False, "reason": "Unknown claim type %r." % claim}

    def critique(self, results):
        """Short text block for feeding back to the hypothesis or experiment agents."""
        if isinstance(results, StatResult):
            results = [results]
        lines = []
        for i, r in enumerate(results, 1):
            title = r.label or r.design or "test %d" % i
            lines.append("[%d] %s -> %s" % (i, title, r.verdict.upper()))
            lines.append("    " + r.explanation)
            for w in r.warnings:
                lines.append("    Warning: " + w)
            for lim in r.limitations:
                lines.append("    Limitation: " + lim)
        return "\n".join(lines)



# ----------------------------------------------------------------------------
# Week 3 Orchestrator Integration Adapter
# ----------------------------------------------------------------------------
def evaluate_experiment_results(
    hypothesis: str,
    experiment_result: dict,
    alpha: float = 0.05,
    test_type: str = "descriptive",
) -> dict:
    if not isinstance(hypothesis, str) or not hypothesis.strip():
        raise ValueError("Hypothesis must be a non-empty string.")
    if not isinstance(experiment_result, dict):
        raise ValueError("experiment_result must be a dictionary.")
    if not (0 < alpha < 1):
        raise ValueError("alpha must be between 0 and 1 exclusive.")

    status = experiment_result.get("status")
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
            "criticism": "Experiment metrics are missing mean, sample_size, or standard_deviation.",
            "recommendations": ["Compute basic descriptive metrics in experiment script."],
        }

    if sample_size < 2:
        return {
            "status": "inconclusive",
            "test_name": test_type,
            "p_value": None,
            "confidence_interval": None,
            "significant": False,
            "assumptions_met": False,
            "criticism": f"Insufficient sample size n={sample_size}. At least 2 observations are required.",
            "recommendations": ["Increase sample size to enable statistical testing."],
        }

    z_crit = 1.96 if abs(alpha - 0.05) < 1e-4 else (2.576 if abs(alpha - 0.01) < 1e-4 else 1.96)
    margin_of_error = z_crit * (std_val / math.sqrt(sample_size))
    ci_lower = round(mean_val - margin_of_error, 4)
    ci_upper = round(mean_val + margin_of_error, 4)

    is_significant = not (ci_lower <= 0.0 <= ci_upper)
    assumptions_met = sample_size >= 3

    criticism = (
        f"Sample size n={sample_size}, Mean={mean_val:.4f}, StdDev={std_val:.4f}. "
        f"95% CI is [{ci_lower:.4f}, {ci_upper:.4f}]."
    )

    recommendations = []
    if sample_size < 10:
        recommendations.append("Sample size is small (n < 10); statistical power is limited.")
    if not assumptions_met:
        recommendations.append("Normality assumptions may be violated for small samples.")

    return {
        "status": "evaluated",
        "test_name": test_type,
        "p_value": None,
        "confidence_interval": [ci_lower, ci_upper],
        "significant": is_significant,
        "assumptions_met": assumptions_met,
        "criticism": criticism,
        "recommendations": recommendations,
    }
