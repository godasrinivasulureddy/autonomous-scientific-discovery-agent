# Autonomous Multimodal Scientific Discovery Agent — Week 4 Demonstration Guide

**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Company:** Zaalima Development Pvt. Ltd.  
**Review Presentation:** Final Demonstration & Internship Handover  
**Team Lead:** Goda Srinivasulu Reddy  
**Date:** November 2026  

---

## 🎯 1. Demonstration Objective
To demonstrate an end-to-end autonomous research workflow that connects:
1. Natural language research query submission.
2. Semantic paper retrieval from Pinecone vector store and live databases (PubMed/ArXiv).
3. Grounded hypothesis generation with traceable bracketed citations (`[1]`, `[2]`).
4. Extracted multimodal chart and plot analysis via Gemini Vision.
5. Controlled empirical code execution inside an isolated Docker sandbox.
6. SciPy statistical evaluation ($p$-values, effect sizes, 95% confidence intervals).
7. Cross-agent context retention via memory management.
8. Automated generation of peer-review-ready Markdown and LaTeX research abstracts.

---

## 🚀 2. Demonstration Step-by-Step Script

### Step 1: Launch the Web Dashboard
Open Command Prompt and run:
```cmd
cd "C:\Zaaalimaaa Scientific discovery Agent"
streamlit run app.py
```
- Open your browser to **`http://localhost:8501`**.

---

### Step 2: Configure Discovery Parameters (Sidebar)
1. **Workflow Mode:** Select `RAG Semantic Retrieval (Pinecone)` (or `Multimodal PDF Analysis`).
2. **Enable Statistical Critic (SciPy):** Checked (`True`).
3. **Enable Cross-Agent Context Memory:** Checked (`True`).
4. **Max Papers to Retrieve:** `3`.

---

### Step 3: Input Research Query & Empirical Benchmark Data
1. **Preset Selection:** Choose `CRISPR-Cas9 off-target cleavage reduction mechanisms`.
2. **Benchmark Data Points:**
   ```text
   12.4, 14.2, 11.8, 15.1, 13.5, 12.9, 14.0
   ```
3. **Multimodal Upload (Optional):** Upload sample PDF (`02 Smart Interview Preparation Assistant Using LLMs.pdf`).

---

### Step 4: Trigger Multi-Agent Collaboration
Click **`🚀 Run Scientific Discovery Workflow`**.
- Walk the reviewer through the real-time stage progression:
  1. `📚 1. Lit Reviewer` (Searching vector embeddings & summarizing findings).
  2. `💡 2. Hypothesis` (Formulating grounded hypotheses with traceable citations).
  3. `👁️ 3. Vision Critic` (Extracting embedded charts and describing visual findings).
  4. `⚡ 4. Code Executor` (Executing experiment script inside Docker sandbox).
  5. `📊 5. Stat Critic` (Running hypothesis tests, confidence intervals, Cohen's d).

---

### Step 5: Walkthrough of Dashboard Output Tabs

1. **📚 Literature & Citations:**
   - Point out structured literature review and citation cards with external URL links.
2. **💡 Hypothesis & Method:**
   - Show how the hypothesis strictly cites literature (`[1]`, `[2]`) with defined independent and dependent variables.
3. **👁️ Multimodal Visuals:**
   - Review extracted figure labels, figure types, and Gemini Vision findings.
4. **⚡ Experiment & Statistical Critic:**
   - Highlight the Docker sandbox execution metadata, $95\%$ Confidence Interval (`[12.57, 14.25]`), power warnings, and $p$-value decisions.
5. **📄 Research Report Export:**
   - Show the synthesized peer-review abstract.
   - Click **📥 Download Report (Markdown)** and **📥 Download Report (LaTeX)** to show download capabilities.
6. **🧠 Cross-Agent Memory:**
   - Show turn-by-turn history retention across all agents.
7. **📊 System Analytics & Cost:**
   - Review token counts, pipeline latency, and estimated Gemini Flash expenditure.

---

## 🛠️ 3. Troubleshooting & Live Backup Commands
If presenting offline without network connectivity:
- Switch **Workflow Mode** to `Direct Literature Input / Text Context`. The pipeline will execute with direct literature text without needing live API calls.
- Run CLI report demo:
  ```cmd
  python -m services.demo_research_report
  ```
- Run automated holdout evaluation benchmark:
  ```cmd
  python -m evaluation.run_evaluation
  ```
- Run automated test suite:
  ```cmd
  pytest tests/test_streamlit_app.py tests/test_research_synthesizer.py tests/test_evaluation_benchmark.py -v
  ```
