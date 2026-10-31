# Week 4 — Architecture Specification & Dashboard Design

**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Company:** Zaalima Development Pvt. Ltd.  
**Sprint:** Week 4 (Final Phase — Interactive Dashboard, Evaluation & Delivery)  
**Author:** Goda Srinivasulu Reddy (Team Lead)  
**Date:** 30–31 October 2026  
**Status:** Approved for Implementation  

---

## 1. Executive Summary & Week 4 Objectives

Week 4 represents the culminating phase of the Autonomous Multimodal Scientific Discovery Agent. Building upon the verified, literature-grounded RAG, hardened Docker sandbox, RL auto-repair, multimodal vision, and statistical critic foundation developed across Weeks 1–3 (282 passing tests), Week 4 delivers:

1. **Interactive Streamlit Web Dashboard (Team Lead — Srinivasulu Reddy):**
   - Real-time research query submission and paper ingestion interface.
   - Live visual tracking of multi-agent execution steps (Literature Reviewer $\rightarrow$ Hypothesis Generator $\rightarrow$ Docker Code Executor $\rightarrow$ Statistical Critic $\rightarrow$ Memory Manager).
   - Traceable citation viewers with Evidence `[N]` bracket expansion and provenance metadata.
   - Multimodal figure inspector displaying extracted research plots and Gemini Vision analyses.
   - Interactive statistical analysis plots (distribution charts, confidence interval error-bars, p-value thresholds).
   - Execution metrics panel displaying Docker sandbox status, runtime latency, and estimated token/API costs.

2. **Automated Research Report Generator (Member 2 — Anand):**
   - Structured export of discovery findings into Markdown and PDF/DOCX formats.
   - Comprehensive evidence appendices, statistical tables, and methodology limitations.

3. **System Benchmarking, Stress Testing & Final Evaluation (Member 3 — Krishna):**
   - Quantitative evaluation of retrieval accuracy, hypothesis groundedness, sandbox security enforcement, and end-to-end latency benchmarks.

---

## 2. Streamlit Dashboard Visual Layout & Information Architecture

The dashboard is structured around an intuitive 5-section workflow matching the scientific research discovery lifecycle:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  🔬 Autonomous Multimodal Scientific Discovery Agent — Research Console          │
│  [Status: Online]  [Branch: Week 4]  [Docker Sandbox: Active]  [Memory: Active]  │
├────────────────────────┬─────────────────────────────────────────────────────────┤
│ ⚙️ SIDEBAR CONTROLS    │ 📊 MAIN DISPLAY WORKSPACE                               │
│                        │                                                         │
│ 1. Research Topic Input│ ── SECTION 1: RESEARCH TOPIC & PIPELINE OVERVIEW ────── │
│    [Text input area]   │ • Real-time status cards (Papers, Chunks, Confidence)   │
│                        │                                                         │
│ 2. Pipeline Settings   │ ── SECTION 2: LIVE MULTI-AGENT EXECUTION PROGRESS ──── │
│    • Ingestion count   │ • Step 1: Ingestion & PyMuPDF (Completed)               │
│    • Top-k retrieval   │ • Step 2: Literature Reviewer Synthesis (Completed)     │
│    • Alpha threshold   │ • Step 3: Evidence-Grounded Hypothesis (Completed)      │
│    • Enable Vision?    │ • Step 4: Docker Code Sandbox Execution (Completed)     │
│    • Enable Critic?    │ • Step 5: Statistical Critic Evaluation (Completed)     │
│                        │ • Step 6: Memory Manager Context Retention (Completed)  │
│ 3. Sample Presets      │                                                         │
│    [CRISPR Gene Edit]  │ ── SECTION 3: GROUNDED EVIDENCE & MULTIMODAL FIGURES ── │
│    [Cancer Oncology]   │ • Bracketed Citations (Evidence [1], Evidence [2]...)   │
│    [Diabetes ML Model] │ • Extracted Figures & Gemini Vision Visual Trends       │
│                        │                                                         │
│ 4. Execution Controls  │ ── SECTION 4: STATISTICAL CRITIQUE & EMPIRICAL RUN ──── │
│    [Run Discovery]     │ • Distribution plots & 95% Confidence Interval errorbar │
│    [Clear Memory]      │ • Hypothesis verdict: SIGNIFICANT / NOT_SIGNIFICANT     │
│                        │                                                         │
│ 5. Export Report       │ ── SECTION 5: SYSTEM METRICS, DOCKER & TOKEN COSTS ──── │
│    [Download Markdown] │ • Execution Latency: 1.24s  |  Docker Sandbox: True     │
│    [Download PDF/DOCX] │ • Prompt Tokens: 1,842     |  Completion Tokens: 410    │
│                        │ • Estimated API Cost: $0.00034                          │
└────────────────────────┴─────────────────────────────────────────────────────────┘
```

---

## 3. Orchestrator Backend API Interface Specifications

To power the Streamlit UI cleanly without tight coupling or code duplication, the dashboard interfaces with the orchestrator via modular, stateless and stateful bridge functions:

### 3.1 Pipeline Execution Bridge (`agents.orchestrator`)

```python
def run_multimodal_research_pipeline(
    research_topic: str,
    pdf_bytes: bytes | None = None,
    paper_id: str = "custom_paper",
    paper_title: str = "",
    experiment_values: list[float] | None = None,
    memory_manager: AgentMemoryManager | None = None,
    enable_statistical_critic: bool = True,
    max_figures: int = 5,
) -> dict[str, Any]
```

**Output Data Schema for UI Rendering:**
```json
{
  "research_topic": "Precision Gene Editing",
  "literature_review": "Synthesized findings, gaps, and methodologies...",
  "hypothesis": "Testable prediction with explicit Evidence [N] references...",
  "multimodal_figures_count": 2,
  "visual_analyses": [
    {
      "figure_id": "paper1_fig_1",
      "reference_label": "Figure 1 (Page 2)",
      "figure_type": "Bar Plot",
      "analysis": "HF1 variant exhibits 88% efficiency in HEK293T..."
    }
  ],
  "experiment": {
    "status": "success",
    "mean": 14.35,
    "standard_deviation": 1.42,
    "sample_size": 6,
    "metadata": {
      "execution_time_seconds": 0.42,
      "docker_sandboxed": true
    }
  },
  "statistical_critic_result": {
    "status": "evaluated",
    "test_name": "descriptive",
    "significant": true,
    "confidence_interval": [13.21, 15.49],
    "assumptions_met": true,
    "criticism": "Sample size n=6, Mean=14.35, 95% CI is [13.21, 15.49]...",
    "recommendations": []
  },
  "memory_context": "Sliding window summary and relevant history tokens..."
}
```

### 3.2 Token and Cost Estimation Engine (`services.cost_tracker`)

The dashboard features an integrated token and cost estimator tracking Google Gemini API usage:

$$\text{Estimated Cost} = \left(\frac{N_{\text{input\_tokens}}}{10^6} \times \$0.15\right) + \left(\frac{N_{\text{output\_tokens}}}{10^6} \times \$0.60\right)$$

- Tracks prompt tokens, completion tokens, and embedding vectors.
- Calculates per-run and cumulative session costs.

---

## 4. Multi-Agent Step Progress Tracking Specification

The Streamlit UI visualizes each agent step in sequence with interactive status spinners, timestamps, and expandable details:

| Step # | Agent / Stage | UI Element | Displayed Information |
|:---:|---|---|---|
| **1** | **Paper Ingestion & Extraction** | `st.status("Ingesting Scientific Literature...")` | Source counts (ArXiv/PubMed), PyMuPDF extracted page count, and chunk count. |
| **2** | **Literature Reviewer Agent** | `st.expander("Literature Review & Gap Analysis")` | Structured markdown with paper citations, method limitations, and research gap. |
| **3** | **Hypothesis Generator Agent** | `st.expander("Evidence-Grounded Hypothesis")` | Testable hypothesis text with clickable `Evidence [N]` reference tooltips. |
| **4** | **Docker Sandbox Execution** | `st.expander("Docker Code Execution Results")` | Raw experiment parameters, execution runtime (s), and non-root sandbox metadata. |
| **5** | **Statistical Critic Agent** | `st.expander("Statistical Evaluation & Confidence Intervals")` | SciPy test verdict (`SIGNIFICANT`), 95% CI visual error bars, and assumptions. |
| **6** | **Agent Memory Manager** | `st.expander("Context Window & Conversation Memory")` | Token budget meter, sliding window history count, and executive background summary. |

---

## 5. Week 4 Work Distribution & Implementation Assignment

| Team Member | Role | Week 4 Deliverables | Assigned Branch |
|---|---|---|---|
| **Goda Srinivasulu Reddy** | **Team Lead** | • Streamlit Dashboard Architecture & UI Implementation (`app.py`, `ui/`)<br>• Real-time Agent Progress, Evidence Viewers, Docker & Cost Trackers<br>• System Integration & Final Review Coordination | `feature/week4-streamlit-dashboard` |
| **Anand Satapara** | **Member 2** | • Automated Scientific Report Generator (`services/report_generator.py`)<br>• Structured Markdown & PDF/DOCX Export Formats<br>• Report Template & Bibliography Builder | `feature/week4-research-reports` |
| **Krishna** | **Member 3** | • End-to-End System Evaluation & Benchmark Suite (`services/system_evaluator.py`)<br>• Retrieval Quality Metrics, Groundedness Verification & Latency Benchmarks<br>• Final Stress Testing & Failure Mode Audits | `feature/week4-testing-evaluation` |

---

## 6. Day-Wise Roadmap for Week 4 (Final Phase)

- **Day 1 (30 Oct):** Planning, Architecture Review, Streamlit UI/API Specification & Branch Initialization.
- **Day 2 (31 Oct):** Core Dashboard Development (Sidebar, Topic Input, Multi-Agent Step Pipeline & Cost Tracker).
- **Day 3 (01 Nov):** Evidence, Citations, Multimodal Figures & Statistical Critic Visualizations.
- **Day 4 (02 Nov):** Comprehensive Dashboard Testing & Failure Mode Handling.
- **Day 5 (03 Nov):** Integration with Report Generator (Member 2) and Benchmark Evaluator (Member 3).
- **Day 6 (04 Nov):** End-to-End System Verification, Final Handover Documentation, and Merge to `main`.
- **Buffer Day (05 Nov):** Final Internship Presentation Rehearsal and Project Submission.
