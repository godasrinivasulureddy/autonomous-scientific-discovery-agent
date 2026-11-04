# Final Architecture & Research Synthesis Report

**Module:** Research Report Synthesis & Architecture Documentation (Week 4, Member 2)  
**Author:** Anand Satapara (Research Reports & Documentation)  
**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Company:** Zaalima Development Pvt. Ltd.  
**Date:** November 2026  
**Status:** ✅ Complete & Verified  

---

## 1. System Architecture Overview

The **Autonomous Multimodal Scientific Discovery Agent** connects paper retrieval, evidence grounding, hypothesis generation, sandboxed execution, statistical critique, and automated report synthesis into a continuous, self-verifying workflow.

```
+-----------------------------------------------------------------------------------+
|                            Multi-Agent Architecture Flow                           |
+-----------------------------------------------------------------------------------+
|  1. Literature Acquisition                                                        |
|     - ArXiv & PubMed Ingestion                                                    |
|     - PyMuPDF Text Cleaning & Chunking                                            |
|     - Gemini Embeddings (768-dim) -> Pinecone Vector Database                     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  2. Grounded Literature Reviewer (Agent 1)                                        |
|     - Semantic search over verified peer-reviewed research papers                 |
|     - Research gap identification & traceable bibliographic metadata              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  3. Multimodal Figure & Plot Critic                                               |
|     - PyMuPDF vector & raster figure extraction                                   |
|     - Gemini Vision analysis of plots, flowcharts, and architecture diagrams     |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  4. Hypothesis Generator (Agent 2)                                                |
|     - Grounded hypothesis formulation with strict bracket citations ([1], [2])   |
|     - Independent/dependent variable definition & verification experiment design |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  5. Docker Code Executor & Auto-Repair (Agent 3)                                  |
|     - Secure, network-isolated container execution                                |
|     - AST syntax and import whitelisting (NumPy, SciPy, Math)                     |
|     - Bounded AI-assisted error correction loop (max 2 retries)                   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  6. Statistical Critic (SciPy Evaluation)                                         |
|     - Automated hypothesis testing (Welch t-test, Mann-Whitney U, ANOVA)          |
|     - p-values, 95% Confidence Intervals, Cohen's d effect sizes                  |
|     - Holm-Bonferroni multi-comparison error rate control                         |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|  7. Research Report Synthesizer (Anand - Week 4)                                  |
|     - Deterministic template-based Markdown & LaTeX abstract generation           |
|     - Automated number checks against raw SciPy results (zero hallucination)      |
|     - Overclaim prevention & peer-verifiable citation mapping                     |
+-----------------------------------------------------------------------------------+
```

---

## 2. Research Synthesizer Design & Guarantees

### Key Design Rule:
> **The generated report cannot say more than the empirical evidence shows.**

1. **Deterministic Template Rendering:**
   Unlike unconstrained language model outputs which frequently hallucinate statistical significance or distort numerical metrics, `agents/research_synthesizer.py` builds the report directly from template functions that pull numbers exclusively from the `Statistical Critic` output.
2. **Citation Grammar & Validation:**
   - Supports bracket styles: `[1]`, `[1, 2]`, `[1][3]`, `[2-4]`.
   - Every cited source is verified against retrieved literature metadata. Uncited sources are cleanly excluded from the bibliography.
3. **Overclaim Word Detection:**
   - Uses regex filters (`OVERCLAIM_RE`) to flag words like *"proves"*, *"proven"*, *"proof"*, *"conclusively"*, or *"definitively"*.
   - Replaces absolute claims with statistically accurate phrasing (*"Statistically significant at alpha = 0.05"* or *"Not statistically significant; this does not show that there is no effect"*).

---

## 3. Supported Features & Formats

- **Export Formats:**
  - **Markdown (`.md`):** Formatted for instant viewing on GitHub, documentation sites, and Streamlit dashboards.
  - **LaTeX (`.tex`):** Complete article class document ready for immediate compilation with `pdflatex` (includes `\documentclass`, abstract, sections, and `\begin{thebibliography}`).
- **Built-in Quality Checks (`report.checks`):**
  - `citations_valid`: Confirms all cited numbers map to actual papers.
  - `p_value_problems`: Confirms every $p$-value in findings matches statistical test results.
  - `overclaim_words`: Flags ungrounded conclusive terminology.
  - `passed`: `True` when all integrity gates pass cleanly.

---

## 4. Known Limitations & Usage Instructions

1. **Human Review Required:** Automated synthesis should serve as an acceleration tool for researchers, not an independent authority. A human domain expert must review findings before publication.
2. **Directional Interpretation:** The conclusion reports the observed direction of effect and advises the researcher to verify it against the theoretical hypothesis.
3. **Setup & Compilation:**
   ```powershell
   # Run the standalone report generator demonstration
   python -m services.demo_research_report

   # Compile generated LaTeX report (run twice for citation resolution)
   pdflatex reports/generated/sample_report.tex
   ```
