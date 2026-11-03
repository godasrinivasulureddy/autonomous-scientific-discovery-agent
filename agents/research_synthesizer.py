"""Research Report Synthesizer (Week 4, Member 2).

Turns a finished research run into a structured research abstract with
citations, statistical findings and limitations, as Markdown and LaTeX.

Design rule: every number in the report comes from the statistical results,
and every citation comes from the retrieved sources. The report text is built
from templates, not written freely by a language model, so it cannot claim more
than the evidence shows. Only the hypothesis text (already checked by the RAG
verifier) is carried over word for word.

Request format (a plain dict)
-----------------------------
{
  "question":   "Does retrieval grounding improve answer accuracy?",
  "hypothesis": "Grounding raises accuracy [1][2]."   # text, or a dict with
                                                       # "text" and "status"
  "sources":    [ {title, authors, year, venue, doi, ...}, ... ],
                # a source's number is its "number" key if present, otherwise
                # its position in the list (1, 2, 3 ...)
  "experiment": {"description": "...", "execution": <executor output>},
  "evaluation": <result of evaluate_experiment_output>,   # optional: computed
                # from experiment["execution"] when missing
  "figures":    [ {"source": 2, "figure": "Figure 3", "finding": "..."} ],
  "limitations": ["extra limitation text"],
  "title": "optional", 
}
"""

import datetime
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from agents.experiment_evaluator import evaluate_experiment_output

CITATION_RE = re.compile(r"\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]")
P_VALUE_RE = re.compile(r"\bp\s*([=<])\s*([0-9]*\.?[0-9]+)")
OVERCLAIM_RE = re.compile(
    r"(?<!not )(?<!n't )\b(proves?|proven|proof|conclusively|definitively|undeniabl\w+|irrefutabl\w+)\b",
    re.IGNORECASE)
SECTION_ORDER = ("Objective", "Methods", "Findings", "Conclusion", "Limitations")

LATEX_SPECIALS = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


@dataclass
class Report:
    status: str = "complete"      # complete | incomplete | invalid_input
    title: str = ""
    date: str = ""
    sections: dict = field(default_factory=dict)      # name -> list of text lines
    references: list = field(default_factory=list)    # [{"number", "text"}]
    checks: dict = field(default_factory=dict)
    markdown: str = ""
    latex: str = ""

    def to_dict(self):
        return asdict(self)


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------

def _field(obj, *names, default=""):
    """First non-empty value among several possible keys or attributes."""
    for name in names:
        value = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
        if value is not None and value != "" and value != []:
            return value
    return default


def parse_citation_numbers(text):
    """Citation numbers used in a text: '[1]', '[1, 2]', '[1][3]', '[2-4]'."""
    numbers = []
    for match in CITATION_RE.finditer(text or ""):
        for part in re.split(r"\s*,\s*", match.group(1)):
            span = re.split(r"\s*[\u2013-]\s*", part)
            if len(span) == 2 and int(span[0]) <= int(span[1]) <= int(span[0]) + 50:
                numbers.extend(range(int(span[0]), int(span[1]) + 1))
            elif part.strip().isdigit():
                numbers.append(int(part))
    return numbers


def latex_escape(text):
    return "".join(LATEX_SPECIALS.get(c, c) for c in str(text))


def _number_sources(sources):
    numbered = {}
    for position, src in enumerate(sources or [], start=1):
        raw = _field(src, "number", "index", "n", "citation_number", "ref", default=None)
        try:
            number = int(raw)
        except (TypeError, ValueError):
            number = position
        numbered[number] = src
    return numbered


def _clean_doi(doi):
    doi = str(doi or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:", "DOI:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi


def format_reference(src, number):
    """One reference as plain text."""
    authors = _field(src, "authors", "author")
    if isinstance(authors, (list, tuple)):
        names = [str(a) for a in authors]
        authors = ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")
    year = _field(src, "year", "published_year")
    if not year:
        found = re.search(r"\b(19|20)\d{2}\b", str(_field(src, "published", "date")))
        year = found.group(0) if found else ""
    head = str(authors).strip()
    if year:
        head = (head + " (%s)" % year).strip()
    title = str(_field(src, "title", default="Untitled source")).strip()
    venue = str(_field(src, "venue", "journal")).strip()
    pieces = [p.rstrip(".") for p in (head, title, venue) if p]
    text = ". ".join(pieces) + "."
    doi = _clean_doi(_field(src, "doi"))
    url = str(_field(src, "url", "link")).strip()
    link = "https://doi.org/" + doi if doi else url
    if link:
        text += " " + link
    return {"number": number, "text": text, "doi": doi, "link": link}


def _stat_symbol(test_used):
    t = str(test_used).lower()
    for key, symbol in (("t-test", "t"), ("mann", "U"), ("wilcoxon", "W"), ("anova", "F"),
                        ("kruskal", "H"), ("pearson", "r"), ("spearman", "rho"),
                        ("chi-square", "chi2"), ("fisher", "odds ratio")):
        if key in t:
            return symbol
    return "statistic"


def _fmt_p(p):
    return "p < 0.0001" if p < 0.0001 else "p = %.4f" % p


def _dedupe(items):
    seen, out = set(), []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


# ----------------------------------------------------------------------------
# Building the sections
# ----------------------------------------------------------------------------

def _finding_line(index, r):
    label = r.get("label") or r.get("design") or "Analysis %d" % index
    if r.get("status") != "ok":
        reason = (r.get("explanation") or "").split(":", 1)[-1].strip().rstrip(".")
        return "%s: could not be evaluated (%s)." % (label, reason or "no usable result")
    parts = ["%s: %s" % (label, r.get("test_used", "statistical test"))]
    if r.get("statistic") is not None:
        parts.append("%s = %.3g" % (_stat_symbol(r.get("test_used")), r["statistic"]))
    parts.append(_fmt_p(r["p_value"]))
    if r.get("adjusted_p_value") is not None:
        parts.append("Holm-adjusted " + _fmt_p(r["adjusted_p_value"]))
    effect = r.get("effect_size") or {}
    if effect:
        parts.append("%s = %s (%s)" % (effect["name"], effect["value"], effect["magnitude"]))
    ci = r.get("confidence_interval") or {}
    if ci:
        parts.append("%g%% CI [%s, %s] for %s" % (round(ci["level"] * 100, 4), ci["low"], ci["high"], ci["what"]))
    line = ", ".join(parts) + "."
    if r.get("direction"):
        line += " " + r["direction"]
    alpha = r.get("alpha", 0.05)
    if r.get("verdict") == "significant":
        line += " Statistically significant at alpha = %g." % alpha
    elif r.get("verdict") == "not_significant":
        line += " Not statistically significant at alpha = %g; this does not show that there is no effect." % alpha
    else:
        line += " No conclusion can be drawn."
    return line


def _conclusion(results, hypothesis_given):
    usable = [r for r in results if r.get("status") == "ok"]
    if not usable:
        return "No statistical conclusion can be drawn because no analysis produced a usable result."
    name = lambda r: r.get("label") or r.get("design") or "analysis"
    sig = [name(r) for r in usable if r.get("verdict") == "significant"]
    non = [name(r) for r in usable if r.get("verdict") == "not_significant"]
    bad = [name(r) for r in results if r.get("status") != "ok"]
    parts = []
    if sig:
        parts.append("Statistically significant results were obtained for: %s." % "; ".join(sig))
    if non:
        parts.append("No statistically significant result was found for: %s. This does not show that "
                     "there is no effect." % "; ".join(non))
    if bad:
        parts.append("These analyses could not be evaluated: %s." % "; ".join(bad))
    if sig:
        parts.append("Significance alone does not establish that the hypothesis is correct; "
                     "the direction and size of each effect should be checked against it.")
    elif hypothesis_given:
        parts.append("The data therefore provide no statistical evidence for the hypothesis.")
    return " ".join(parts)


def _methods(experiment, evaluation, results):
    lines = []
    desc = _field(experiment, "description", "design", "summary") if experiment else ""
    lines.append("Experiment: %s" % desc if desc else "Experiment: no description was provided.")
    execution = experiment.get("execution") if isinstance(experiment, dict) else None
    if isinstance(execution, dict) and execution.get("success") is True:
        attempts = execution.get("attempts")
        extra = " after %d attempt(s)" % attempts if isinstance(attempts, int) and attempts > 0 else ""
        lines.append("Execution: completed successfully%s." % extra)
    usable = [r for r in results if r.get("status") == "ok"]
    if usable:
        tests = _dedupe([r.get("test_used") for r in usable])
        alphas = _dedupe(["%g" % r.get("alpha", 0.05) for r in usable])
        alpha_text = alphas[0] if len(alphas) == 1 else "set per analysis"
        lines.append("Statistical analysis: %s (two-sided, alpha = %s)." % ("; ".join(tests), alpha_text))
        if any(r.get("adjusted_p_value") is not None for r in usable):
            lines.append("Holm-Bonferroni correction was applied across %d analyses." % len(usable))
        sizes = []
        for i, r in enumerate(usable, 1):
            if r.get("sample_sizes"):
                label = r.get("label") or "Analysis %d" % i
                sizes.append("%s: %s" % (label, ", ".join("%s = %d" % kv for kv in r["sample_sizes"].items())))
        if sizes:
            lines.append("Sample sizes: " + "; ".join(sizes) + ".")
    return lines


def _figure_lines(figures, numbered):
    """Resolve figure findings to cited sources. Returns (lines, cited, unresolved)."""
    lines, cited, unresolved = [], [], []
    for fig in figures or []:
        number = None
        raw = _field(fig, "source", "citation", "number", default=None)
        try:
            number = int(raw)
        except (TypeError, ValueError):
            key = str(_field(fig, "paper_id", "doi", "id"))
            for n, src in numbered.items():
                ids = [str(_field(src, k)) for k in ("id", "paper_id", "arxiv_id", "pmid", "doi")]
                if key and key in ids:
                    number = n
                    break
        finding = str(_field(fig, "finding", "summary", "description", "analysis")).strip()
        figure = str(_field(fig, "figure", "figure_ref", "label", default="A figure")).strip()
        if number in numbered and finding:
            cited.append(number)
            lines.append("Automated figure analysis, %s of [%d]: %s" % (figure, number, finding))
        else:
            unresolved.append(figure)
    return lines, cited, unresolved


def generate_report(request, date=None):
    """Build the report from a request dict. Never raises on bad input."""
    report = Report(date=date or datetime.date.today().isoformat())
    if not isinstance(request, dict):
        report.status = "invalid_input"
        report.checks = {"error": "The request must be a dict."}
        return report

    question = str(request.get("question") or "").strip()
    hyp = request.get("hypothesis")
    hyp_status = ""
    if isinstance(hyp, dict):
        hyp_status = str(hyp.get("status") or "")
        hyp_text = str(_field(hyp, "text", "hypothesis", "answer")).strip()
        sources = request.get("sources") or hyp.get("references") or hyp.get("sources")
    else:
        hyp_text = str(hyp or "").strip()
        sources = request.get("sources")
    if not question and not hyp_text:
        report.status = "invalid_input"
        report.checks = {"error": "Give at least a 'question' or a 'hypothesis'."}
        return report

    numbered = _number_sources(sources)
    experiment = request.get("experiment") if isinstance(request.get("experiment"), dict) else {}
    evaluation = request.get("evaluation")
    if evaluation is None and isinstance(experiment.get("execution"), (dict, str)):
        evaluation = evaluate_experiment_output(experiment["execution"])
    if isinstance(evaluation, list):
        evaluation = {"status": "ok", "results": evaluation}
    evaluation = evaluation if isinstance(evaluation, dict) else {"status": "no_statistics_found",
                                                                  "reason": "No evaluation was provided.", "results": []}
    results = list(evaluation.get("results") or [])

    figure_lines, figure_cited, unresolved = _figure_lines(request.get("figures"), numbered)
    cited = sorted(set(parse_citation_numbers(hyp_text)) | set(figure_cited))
    missing = [n for n in cited if n not in numbered]
    references = [dict(format_reference(numbered[n], n)) for n in cited if n in numbered]
    no_doi = [r["number"] for r in references if not r["doi"]]

    # --- sections -----------------------------------------------------------
    objective = []
    if question:
        objective.append("Research question: %s" % question)
    if hyp_text:
        objective.append("Hypothesis: %s" % hyp_text)
    if references:
        objective.append("Evidence base: %d cited source(s)." % len(references))
    findings = [_finding_line(i, r) for i, r in enumerate(results, 1)] + figure_lines
    if not results:
        findings.insert(0, "No statistical results are available (%s)." %
                        (evaluation.get("reason") or "the experiment produced none").rstrip("."))

    limitations = []
    if hyp_status and hyp_status.lower() != "grounded":
        limitations.append("The hypothesis was not fully grounded in the retrieved literature (status: %s)." % hyp_status)
    if evaluation.get("status") != "ok" and evaluation.get("reason"):
        limitations.append(str(evaluation["reason"]))
    for i, r in enumerate(results, 1):
        label = r.get("label") or r.get("design") or "Analysis %d" % i
        limitations.extend("%s: %s" % (label, w) for w in r.get("warnings", []))
    for r in results:
        limitations.extend(r.get("limitations", []))
    limitations.extend(str(x) for x in request.get("limitations") or [])
    limitations.extend("Citation [%d] has no matching source in the source list." % n for n in missing)
    if unresolved:
        limitations.append("%d figure finding(s) could not be linked to a cited source and were left out." % len(unresolved))
    limitations.extend("Source [%d] has no DOI." % n for n in no_doi)
    limitations.append("This report was generated automatically from the experiment outputs and retrieved "
                       "literature and should be reviewed by a person before it is relied on.")

    report.sections = {
        "Objective": objective,
        "Methods": _methods(experiment, evaluation, results),
        "Findings": findings,
        "Conclusion": [_conclusion(results, bool(hyp_text))],
        "Limitations": _dedupe(limitations),
    }
    report.references = references
    report.status = "complete" if any(r.get("status") == "ok" for r in results) else "incomplete"
    report.title = str(request.get("title") or "Research report: %s" % (question or hyp_text)[:120])

    report.markdown = _to_markdown(report)
    report.latex = _to_latex(report)
    report.checks = {
        "citations_valid": not missing,
        "missing_citation_numbers": missing,
        "unresolved_figures": unresolved,
        "sources_without_doi": no_doi,
        "uncited_sources_left_out": sorted(set(numbered) - set(cited)),
        "p_value_problems": verify_numbers(report.sections["Findings"], results),
        "overclaim_words": find_overclaims(report.markdown),
    }
    report.checks["passed"] = (report.checks["citations_valid"] and not report.checks["p_value_problems"]
                               and not report.checks["overclaim_words"])
    return report


# ----------------------------------------------------------------------------
# Checks (also usable on a hand-edited report)
# ----------------------------------------------------------------------------

def verify_numbers(findings_lines, results):
    """Every p-value written in the findings must match a statistical result."""
    allowed = set()
    for r in results:
        for key in ("p_value", "adjusted_p_value"):
            v = r.get(key)
            if v is not None:
                allowed.add(("<", "0.0001") if v < 0.0001 else ("=", "%.4f" % v))
    problems = []
    for line in findings_lines:
        if line.startswith("Automated figure analysis"):
            continue
        for op, value in P_VALUE_RE.findall(line):
            try:
                value = "%.4f" % float(value)
            except ValueError:
                continue
            if (op, value) not in allowed and (op, value) != ("<", "0.0001"):
                problems.append("p %s %s does not match any statistical result" % (op, value))
    return problems


def find_overclaims(text):
    """Words such as 'proves' or 'conclusively' that the evidence cannot justify."""
    return sorted(set(m.group(1).lower() for m in OVERCLAIM_RE.finditer(text or "")))


def verify_markdown(markdown, evaluation):
    """Re-check a (possibly hand-edited) Markdown report against the evaluation."""
    results = evaluation.get("results", []) if isinstance(evaluation, dict) else list(evaluation or [])
    match = re.search(r"## Findings\n(.*?)(?=\n## |\Z)", markdown, re.DOTALL)
    lines = [l[2:] for l in (match.group(1).splitlines() if match else []) if l.startswith("- ")]
    return {"p_value_problems": verify_numbers(lines, results), "overclaim_words": find_overclaims(markdown)}


# ----------------------------------------------------------------------------
# Output formats
# ----------------------------------------------------------------------------

def _to_markdown(report):
    out = ["# %s" % report.title, "",
           "*Generated automatically on %s by the Autonomous Multimodal Scientific Discovery Agent. "
           "Status: %s.*" % (report.date, report.status), ""]
    for name in SECTION_ORDER:
        lines = report.sections.get(name, [])
        out.append("## %s" % name)
        if name in ("Methods", "Findings", "Limitations"):
            out.extend("- %s" % l for l in lines)
        else:
            out.append("\n\n".join(lines))
        out.append("")
    if report.references:
        out.append("## References")
        out.extend("[%d] %s" % (r["number"], r["text"]) for r in report.references)
        out.append("")
    return "\n".join(out)


def _tex(text, available):
    escaped = latex_escape(text)

    def cite(match):
        numbers = parse_citation_numbers(match.group(0))
        if numbers and all(n in available for n in numbers):
            return "\\cite{%s}" % ",".join("src%d" % n for n in numbers)
        return match.group(0)
    return CITATION_RE.sub(cite, escaped)


def _to_latex(report):
    available = {r["number"] for r in report.references}
    s = report.sections
    abstract = " ".join(
        [l.replace("Research question: ", "", 1) for l in s["Objective"][:1]] + s["Conclusion"])
    out = [r"\documentclass[11pt]{article}",
           r"\usepackage[T1]{fontenc}",
           r"\usepackage[utf8]{inputenc}",
           r"\usepackage[margin=1in]{geometry}",
           r"\usepackage{hyperref}",
           r"\title{%s}" % latex_escape(report.title),
           r"\author{Autonomous Multimodal Scientific Discovery Agent}",
           r"\date{%s}" % latex_escape(report.date),
           r"\begin{document}", r"\maketitle",
           r"\begin{abstract}", _tex(abstract, available), r"\end{abstract}"]
    for name in SECTION_ORDER:
        out.append(r"\section{%s}" % name)
        lines = s.get(name, [])
        if name in ("Methods", "Findings", "Limitations"):
            out.append(r"\begin{itemize}")
            out.extend(r"\item %s" % _tex(l, available) for l in lines)
            out.append(r"\end{itemize}")
        else:
            out.extend(_tex(l, available) + "\n" for l in lines)
    if report.references:
        out.append(r"\begin{thebibliography}{99}")
        for r in report.references:
            text = latex_escape(r["text"].replace(r["link"], "").strip()) if r["link"] else latex_escape(r["text"])
            link = r"\url{%s}" % r["link"].replace("%", r"\%").replace("#", r"\#") if r["link"] else ""
            out.append(r"\bibitem{src%d} %s %s" % (r["number"], text, link))
        out.append(r"\end{thebibliography}")
    out.append(r"\end{document}")
    return "\n".join(out) + "\n"


def save_report(report, folder, name="research_report"):
    """Write the .md and .tex files. Returns their paths (empty if the report is invalid)."""
    if report.status == "invalid_input":
        return {}
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = {"markdown": folder / (name + ".md"), "latex": folder / (name + ".tex")}
    paths["markdown"].write_text(report.markdown, encoding="utf-8")
    paths["latex"].write_text(report.latex, encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}
