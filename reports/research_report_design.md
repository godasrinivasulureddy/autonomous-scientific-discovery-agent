# Research report synthesis: design and usage

Module: `agents/research_synthesizer.py` | Tests: `tests/test_research_synthesizer.py` |
Demo: `python -m services.demo_research_report` (writes `reports/generated/sample_report.md` and `.tex`)

## Purpose
Turn a finished research run (question, hypothesis, retrieved sources, experiment output and statistical
results) into a structured research abstract with citations, findings and limitations, as Markdown and LaTeX.

## Design rule: the report cannot say more than the evidence
The text is built from templates, not written freely by a language model. Every number comes from the
statistical results and every citation from the retrieved sources. Only the hypothesis text is carried over
unchanged, and it has already been checked by the RAG verifier.

## Structure
| Section | Built from |
|---|---|
| Objective | research question, hypothesis text (with its citations), number of cited sources |
| Methods | experiment description, execution result, tests used, alpha, Holm correction, sample sizes |
| Findings | one line per analysis: test, statistic, p-value, effect size, confidence interval, direction, verdict; optional figure findings tied to a cited source |
| Conclusion | derived from the verdicts only; never says the hypothesis is proven |
| Limitations | warnings and limitations from the statistics, data problems, ungrounded hypothesis, missing DOIs, unresolved citations or figures, and a note that a person must review the report |
| References | only sources actually cited, in citation order, with DOI links |

## Citation rules
- Citations in the hypothesis text look like `[1]`, `[1, 2]`, `[1][3]` or `[2-4]`.
- A source's number is its `number` key, or its position in the source list (1, 2, 3...).
- Sources that are not cited are left out of the references.
- A citation with no matching source is listed in the limitations and fails the report check.
- Figure findings must be linked to a cited source (by `source` number, or by a matching DOI or id).
  Findings that cannot be linked are left out and listed in the limitations.

## Built-in checks (`report.checks`)
- `citations_valid`: every cited number has a source.
- `p_value_problems`: every p-value in the Findings matches a statistical result.
- `overclaim_words`: words such as "proves" or "conclusively" (negations such as "does not prove" are fine).
- `sources_without_doi`, `unresolved_figures`, `uncited_sources_left_out`: information for review.
- `passed`: true when the three main checks are clean.

`verify_markdown(markdown, evaluation)` repeats the p-value and wording checks on a hand-edited report.

## Report status
- `complete`: at least one analysis produced a usable result.
- `incomplete`: no usable statistics (failed experiment, bad data). The report says so plainly.
- `invalid_input`: neither a question nor a hypothesis was given. Nothing is written.

## Usage
```python
from agents.research_synthesizer import generate_report, save_report

report = generate_report({
    "question": "...", "hypothesis": {"text": "... [1]", "status": "grounded"},
    "sources": [...], "experiment": {"description": "...", "execution": executor_output},
})
print(report.checks["passed"])
save_report(report, "reports/generated", name="run_001")
```
If `evaluation` is not given, it is computed from `experiment["execution"]` with
`agents/experiment_evaluator.py`.

## LaTeX
`report.latex` is a complete article (abstract, sections, `thebibliography`). Compile with
`pdflatex file.tex` (run twice so citations resolve). Special characters are escaped; `[n]` becomes
`\cite{srcN}` when the source exists.

## Known limitations
- Report wording is fixed by templates, so it reads plainly rather than elegantly.
- The conclusion does not decide whether an effect points the way the hypothesis predicts; it reports
  the direction and asks the reader to check it.
- Source fields are read from common names (`title`, `authors`, `year`, `venue`, `doi`, `url`); other
  field names need a small mapping.
- Figure findings come from automated image analysis and are labelled as such.
