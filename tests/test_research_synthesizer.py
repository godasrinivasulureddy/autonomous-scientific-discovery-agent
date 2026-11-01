"""Tests for agents/research_synthesizer.py."""

import json

import pytest

from agents.experiment_evaluator import evaluate_experiment_output
from agents.research_synthesizer import (
    find_overclaims,
    format_reference,
    generate_report,
    latex_escape,
    parse_citation_numbers,
    save_report,
    verify_markdown,
    verify_numbers,
)

GROUPED = {"label": "Accuracy: grounded vs ungrounded", "groups": {
    "grounded": [0.86, 0.88, 0.85, 0.87, 0.89, 0.86, 0.88, 0.87],
    "ungrounded": [0.81, 0.83, 0.80, 0.82, 0.84, 0.81, 0.83, 0.82]}}
NOT_SIG = {"label": "Latency", "groups": {"A": [1, 2, 3, 4, 5], "B": [3, 4, 5, 6, 7]}}

SOURCES = [
    {"title": "Retrieval-augmented generation", "authors": ["Lewis", "Perez", "Piktus", "Petroni"],
     "year": 2020, "venue": "NeurIPS", "doi": "10.5555/3495724.3496517"},
    {"title": "Survey of hallucination", "authors": ["Ji", "Lee"], "year": 2023,
     "venue": "ACM Computing Surveys", "doi": "doi:10.1145/3571730"},
    {"title": "Never cited", "year": 2022, "venue": "X", "doi": "10.1/none"},
]


def request(**extra):
    req = {
        "question": "Does retrieval grounding improve accuracy?",
        "hypothesis": {"text": "Grounding raises accuracy [1][2].", "status": "grounded"},
        "sources": SOURCES,
        "experiment": {"description": "Eight runs per model.",
                       "execution": {"success": True, "attempts": 2, "stats": [GROUPED]}},
    }
    req.update(extra)
    return req


# ------------------------------------------------------------------ helpers

@pytest.mark.parametrize("text,expected", [
    ("a [1] b", [1]),
    ("a [1][3] b", [1, 3]),
    ("a [1, 2] b", [1, 2]),
    ("a [2-4] b", [2, 3, 4]),
    ("a [2\u20134] b", [2, 3, 4]),
    ("no citations here", []),
    ("array[i] and [x]", []),
    (None, []),
])
def test_parse_citation_numbers(text, expected):
    assert parse_citation_numbers(text) == expected


def test_latex_escape():
    assert latex_escape("50% of A_B & #1 {x}") == r"50\% of A\_B \& \#1 \{x\}"
    assert latex_escape("a~b^c$") == r"a\textasciitilde{}b\textasciicircum{}c\$"


def test_format_reference_full_and_missing_fields():
    ref = format_reference(SOURCES[0], 1)
    assert ref["text"] == ("Lewis, Perez, Piktus et al. (2020). Retrieval-augmented generation. "
                           "NeurIPS. https://doi.org/10.5555/3495724.3496517")
    assert format_reference(SOURCES[1], 2)["doi"] == "10.1145/3571730"
    bare = format_reference({"title": "Only a title"}, 5)
    assert bare["text"] == "Only a title." and bare["doi"] == ""
    assert "Untitled source" in format_reference({}, 1)["text"]


def test_year_found_in_date_field():
    assert "(2021)" in format_reference({"title": "T", "published": "2021-03-04"}, 1)["text"]


# ------------------------------------------------------------- main report

def test_complete_report_has_all_sections():
    r = generate_report(request(), date="2026-10-31")
    assert r.status == "complete"
    assert list(r.sections) == ["Objective", "Methods", "Findings", "Conclusion", "Limitations"]
    for name in r.sections:
        assert r.sections[name], name
    assert "2026-10-31" in r.markdown
    for heading in ("## Objective", "## Methods", "## Findings", "## Conclusion",
                    "## Limitations", "## References"):
        assert heading in r.markdown


def test_findings_use_actual_statistics():
    r = generate_report(request())
    evaluation = evaluate_experiment_output({"stats": [GROUPED]})
    p = evaluation["results"][0]["p_value"]
    line = r.sections["Findings"][0]
    assert p < 0.0001 and "p < 0.0001" in line
    assert "Welch two-sample t-test" in line
    assert "Cohen's d" in line and "95% CI" in line
    assert "grounded has the higher mean" in line   # direction of the effect is reported


def test_non_significant_result_is_worded_carefully():
    r = generate_report(request(experiment={"execution": {"stats": [NOT_SIG]}}))
    assert "p = 0.0805" in r.sections["Findings"][0]
    assert "Not statistically significant" in r.sections["Findings"][0]
    assert "no statistical evidence" in r.sections["Conclusion"][0]
    assert "does not show that there is no effect" in r.sections["Conclusion"][0]


def test_mixed_results_are_listed_separately():
    r = generate_report(request(experiment={"execution": {"stats": [GROUPED, NOT_SIG]}}))
    concl = r.sections["Conclusion"][0]
    assert "significant results were obtained for: Accuracy" in concl
    assert "No statistically significant result was found for: Latency" in concl
    assert "Holm-Bonferroni" in " ".join(r.sections["Methods"])


def test_evaluation_can_be_supplied_directly():
    evaluation = evaluate_experiment_output({"stats": [GROUPED]})
    r = generate_report(request(experiment={"description": "d"}, evaluation=evaluation))
    assert r.status == "complete"
    assert "Experiment: d" in r.sections["Methods"][0]


def test_methods_describe_the_analysis():
    methods = " ".join(generate_report(request()).sections["Methods"])
    assert "completed successfully after 2 attempt(s)" in methods
    assert "two-sided, alpha = 0.05" in methods
    assert "grounded = 8, ungrounded = 8" in methods


# ---------------------------------------------------------------- citations

def test_references_contain_only_cited_sources():
    r = generate_report(request())
    assert [ref["number"] for ref in r.references] == [1, 2]
    assert "Never cited" not in r.markdown
    assert r.checks["uncited_sources_left_out"] == [3]
    assert r.checks["citations_valid"] is True


def test_citation_to_missing_source_is_reported():
    r = generate_report(request(hypothesis="Claim [1] and [9]."))
    assert r.checks["citations_valid"] is False
    assert r.checks["missing_citation_numbers"] == [9]
    assert any("Citation [9]" in l for l in r.sections["Limitations"])
    assert r.checks["passed"] is False


def test_source_numbers_can_be_given_explicitly():
    sources = [dict(SOURCES[0], number=4), dict(SOURCES[1], number=7)]
    r = generate_report(request(hypothesis="Claims [4] and [7].", sources=sources))
    assert [ref["number"] for ref in r.references] == [4, 7]
    assert r.checks["citations_valid"] is True


def test_sources_inside_hypothesis_dict():
    hyp = {"text": "Claim [1].", "status": "grounded", "references": SOURCES[:1]}
    r = generate_report({"question": "q", "hypothesis": hyp})
    assert [ref["number"] for ref in r.references] == [1]


def test_source_without_doi_is_flagged():
    sources = [{"title": "No DOI paper", "year": 2021}]
    r = generate_report(request(hypothesis="Claim [1].", sources=sources))
    assert r.checks["sources_without_doi"] == [1]
    assert "Source [1] has no DOI." in r.sections["Limitations"]


def test_figure_findings_are_linked_to_sources():
    figures = [{"source": 2, "figure": "Figure 3", "finding": "error falls with depth"},
               {"paper_id": "zzz", "figure": "Figure 9", "finding": "orphan"}]
    r = generate_report(request(figures=figures))
    assert any("Figure 3 of [2]: error falls with depth" in l for l in r.sections["Findings"])
    assert "orphan" not in r.markdown
    assert r.checks["unresolved_figures"] == ["Figure 9"]


def test_figure_can_be_matched_by_doi():
    figures = [{"doi": "10.5555/3495724.3496517", "figure": "Figure 1", "finding": "trend"}]
    r = generate_report(request(figures=figures, hypothesis="No citations here."))
    assert [ref["number"] for ref in r.references] == [1]


# ------------------------------------------------------ honest incomplete runs

def test_failed_experiment_gives_incomplete_report():
    r = generate_report(request(experiment={"execution": {"success": False, "error": "boom"}}))
    assert r.status == "incomplete"
    assert "No statistical results are available" in r.sections["Findings"][0]
    assert "no statistical conclusion" in r.sections["Conclusion"][0].lower()
    assert any("did not run successfully" in l for l in r.sections["Limitations"])


def test_bad_data_analysis_is_reported_not_hidden():
    bad = {"label": "Broken", "groups": {"A": [1, "x", 3], "B": [1, 2, 3]}}
    r = generate_report(request(experiment={"execution": {"stats": [bad, NOT_SIG]}}))
    assert r.status == "complete"
    assert "Broken: could not be evaluated" in " ".join(r.sections["Findings"])
    assert "could not be evaluated: Broken" in r.sections["Conclusion"][0]


def test_ungrounded_hypothesis_is_a_limitation():
    r = generate_report(request(hypothesis={"text": "Claim [1].", "status": "ungrounded"}))
    assert any("not fully grounded" in l for l in r.sections["Limitations"])


def test_extra_limitations_and_warnings_are_included_once():
    r = generate_report(request(limitations=["Only eight runs."]))
    assert "Only eight runs." in r.sections["Limitations"]
    assert len(r.sections["Limitations"]) == len(set(r.sections["Limitations"]))


def test_invalid_inputs():
    assert generate_report(None).status == "invalid_input"
    assert generate_report({}).status == "invalid_input"
    assert generate_report({"sources": SOURCES}).status == "invalid_input"


def test_report_without_any_evaluation():
    r = generate_report({"question": "q", "hypothesis": "h [1]", "sources": SOURCES})
    assert r.status == "incomplete"


# ------------------------------------------------------------------- checks

def test_checks_pass_for_a_clean_report():
    r = generate_report(request())
    assert r.checks["p_value_problems"] == []
    assert r.checks["overclaim_words"] == []
    assert r.checks["passed"] is True


def test_overclaim_words_are_detected_but_negations_are_fine():
    assert find_overclaims("This proves the hypothesis conclusively.") == ["conclusively", "proves"]
    assert find_overclaims("This does not prove anything; it is not proven.") == []
    r = generate_report(request(hypothesis="Grounding proves accuracy [1]."))
    assert r.checks["overclaim_words"] == ["proves"]
    assert r.checks["passed"] is False


def test_verify_numbers_catches_wrong_p_values():
    results = evaluate_experiment_output({"stats": [NOT_SIG]})["results"]
    assert verify_numbers(["Latency: p = 0.0805."], results) == []
    problems = verify_numbers(["Latency: p = 0.0123."], results)
    assert problems and "0.0123" in problems[0]


def test_verify_markdown_detects_hand_edits():
    evaluation = evaluate_experiment_output({"stats": [NOT_SIG]})
    md = generate_report(request(experiment={"execution": {"stats": [NOT_SIG]}})).markdown
    assert verify_markdown(md, evaluation) == {"p_value_problems": [], "overclaim_words": []}
    edited = md.replace("p = 0.0805", "p = 0.0105").replace("Not statistically", "This proves it is")
    out = verify_markdown(edited, evaluation)
    assert out["p_value_problems"] and out["overclaim_words"] == ["proves"]


def test_literature_p_values_in_hypothesis_are_not_flagged():
    r = generate_report(request(hypothesis="Paper [1] reported p = 0.03."))
    assert r.checks["p_value_problems"] == []


# ------------------------------------------------------------------- output

def test_latex_structure_and_citations():
    r = generate_report(request())
    tex = r.latex
    assert tex.startswith(r"\documentclass") and tex.rstrip().endswith(r"\end{document}")
    assert r"\begin{abstract}" in tex and r"\section{Findings}" in tex
    assert r"\cite{src1}\cite{src2}" in tex
    assert r"\bibitem{src1}" in tex and r"\bibitem{src2}" in tex
    assert r"\bibitem{src3}" not in tex
    assert r"\usepackage[T1]{fontenc}" in tex          # makes '<' print correctly
    assert r"95\% CI" in tex


def test_latex_leaves_unknown_citations_as_text():
    r = generate_report(request(hypothesis="Claim [1] and [9]."))
    assert r"\cite{src1}" in r.latex and "[9]" in r.latex


def test_latex_without_references_has_no_bibliography():
    r = generate_report({"question": "q", "hypothesis": "plain text", "evaluation": {"results": []}})
    assert "thebibliography" not in r.latex


def test_special_characters_are_escaped_in_latex():
    r = generate_report(request(question="Does A & B reach 50% accuracy_gain?"))
    assert r"A \& B reach 50\% accuracy\_gain?" in r.latex


def test_save_report_writes_both_files(tmp_path):
    r = generate_report(request())
    paths = save_report(r, tmp_path / "out", name="demo")
    assert (tmp_path / "out" / "demo.md").read_text(encoding="utf-8") == r.markdown
    assert (tmp_path / "out" / "demo.tex").read_text(encoding="utf-8") == r.latex
    assert set(paths) == {"markdown", "latex"}


def test_save_report_skips_invalid_reports(tmp_path):
    assert save_report(generate_report({}), tmp_path) == {}


def test_report_is_json_serialisable():
    data = json.loads(json.dumps(generate_report(request()).to_dict()))
    assert data["status"] == "complete" and data["checks"]["passed"] is True
