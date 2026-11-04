"""Demo of the research report generator. Run from the repo root:

    python -m services.demo_research_report

Writes reports/generated/sample_report.md and sample_report.tex.
"""

from agents.research_synthesizer import generate_report, save_report

sources = [
    {"title": "Retrieval-augmented generation for knowledge-intensive NLP tasks",
     "authors": ["Lewis", "Perez", "Piktus", "Petroni"], "year": 2020,
     "venue": "NeurIPS", "doi": "10.5555/3495724.3496517"},
    {"title": "Survey of hallucination in natural language generation",
     "authors": ["Ji", "Lee"], "year": 2023, "venue": "ACM Computing Surveys",
     "doi": "10.1145/3571730"},
    {"title": "A paper that the hypothesis does not cite", "year": 2022, "venue": "Example Journal",
     "doi": "10.1000/example"},
]

experiment_output = {
    "success": True,
    "attempts": 2,
    "stats": [
        {"label": "Accuracy: grounded vs ungrounded",
         "groups": {"grounded": [0.86, 0.88, 0.85, 0.87, 0.89, 0.86, 0.88, 0.87],
                    "ungrounded": [0.81, 0.83, 0.80, 0.82, 0.84, 0.81, 0.83, 0.82]}},
        {"label": "Latency: grounded vs ungrounded (seconds)",
         "groups": {"grounded": [2.1, 2.4, 2.2, 2.5, 2.3, 2.2], "ungrounded": [2.0, 2.3, 2.2, 2.4, 2.1, 2.3]}},
    ],
}

report = generate_report({
    "question": "Does grounding answers in peer-reviewed literature improve accuracy?",
    "hypothesis": {"text": "Grounding answers in peer-reviewed sources raises answer accuracy [1][2].",
                   "status": "grounded"},
    "sources": sources,
    "experiment": {"description": "Eight runs per condition on the same question set.",
                   "execution": experiment_output},
    "figures": [{"source": 2, "figure": "Figure 3",
                 "finding": "hallucination rate falls as retrieval depth increases"}],
})

print(report.markdown)
print("Checks:", report.checks)
paths = save_report(report, "reports/generated", name="sample_report")
print("Saved:", paths)
