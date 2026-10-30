# Week 3 — Multi-Agent Integration Demo Walkthrough

**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Focus:** Multimodal Vision, Memory-Augmented Orchestration & Statistical Critic Evaluation  
**Date:** October 30, 2026  

---

## 1. Overview

This walkthrough demonstrates the end-to-end multi-agent scientific discovery pipeline integrating:
- **Multimodal Gemini Vision:** Extracting and analyzing figures from research PDFs.
- **Agent Memory Manager:** Sliding-window context retention and query-based relevant history retrieval.
- **Statistical Critic Agent:** Rigorous hypothesis evaluation with confidence intervals, p-values, and assumptions.

---

## 2. Interactive Python Walkthrough

### Scenario: Multimodal PCR & Electrophoresis Experiment

```python
from agents.orchestrator import run_multimodal_research_pipeline
from agents.memory_manager import AgentMemoryManager

# 1. Initialize context-window memory manager
memory = AgentMemoryManager(max_tokens=4000, max_entries=10)

# 2. Load scientific PDF bytes (e.g. from research paper)
with open("data/sample_paper.pdf", "rb") as f:
    pdf_bytes = f.read()

# 3. Execute integrated multimodal research pipeline
result = run_multimodal_research_pipeline(
    research_topic="Quantitative PCR and Amplicon Band Intensity",
    pdf_bytes=pdf_bytes,
    paper_id="pubmed:3891024",
    paper_title="Fluorometric Analysis of Amplified Genomic Fragments",
    experiment_values=[12.4, 15.1, 14.8, 16.2, 13.9, 15.5],
    memory_manager=memory,
    enable_statistical_critic=True,
    max_figures=3,
)

# 4. Inspect Results
print("Literature Review:", result["literature_review"])
print("Grounded Hypothesis:", result["hypothesis"])
print("Multimodal Figures Extracted:", result["multimodal_figures_count"])
print("Visual Analyses:", result["visual_analyses"])
print("Experiment Execution Status:", result["experiment"]["status"])
print("Statistical Critic Verdict:", result["statistical_critic_result"])
print("Memory Context Retained:\n", result["memory_context"])
```

---

## 3. Automated Test Verification Commands

Run targeted and full test suites:
```powershell
# Run Week 3 integration tests
python -m pytest tests/test_week3_integration.py -v

# Run Multimodal Vision tests
python -m pytest tests/test_multimodal_vision.py -v

# Run Statistical Evaluator tests
python -m pytest tests/test_experiment_evaluator.py -v

# Run the complete test suite (281 tests)
python -m pytest tests/ -q
```
**Expected Outcome:** 281 passed in ~7.8s with 0 failures.
