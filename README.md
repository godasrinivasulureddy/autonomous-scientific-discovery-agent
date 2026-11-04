# Autonomous Multimodal Scientific Discovery Agent

An end-to-end, enterprise-grade AI-powered autonomous scientific discovery framework that continuously ingests peer-reviewed literature, grounds research hypotheses in verifiable citations, analyzes scientific charts and figures using multimodal vision, executes empirical code inside a hardened Docker sandbox, evaluates findings using rigorous statistical tests, maintains conversational memory context, and synthesizes peer-review-ready research abstracts in Markdown and LaTeX with an interactive Streamlit monitoring dashboard.

---

## 👥 Project Team

**Organization:** Zaalima Development Pvt. Ltd. (Internship Foundation)  
**Project Duration:** 30 October – 6 November 2026 (Final Project Handover)  
**Team Size:** 3 Members  

| Member | Role | Primary Modules & Responsibilities |
|---|---|---|
| **Goda Srinivasulu Reddy** | **Team Lead** | Full System Integration, Streamlit Dashboard UI, Agent Memory Manager, Cost & Token Tracking, Bounded Code Repair & Orchestration |
| **Anand Satapara** | **Member 2** | Scientific Paper Ingestion (ArXiv/PubMed), Research Report Synthesizer (Markdown & LaTeX), Statistical Critic Agent (SciPy) |
| **Krishna** | **Member 3** | Pinecone Vector Database, Multimodal Gemini Vision (Figure Extraction), Hardened Docker Sandbox, Holdout Benchmark & Evaluation Suite |

---

## 🎯 Final Project Roadmap & Delivery Status

### 🏆 Week 4 Status: 100% Completed & Merged into `main` (November 6, 2026)
- **Goal:** Complete the Streamlit dashboard, research report generation, final system integration, evaluation benchmarks, and project documentation.
- **Key Milestones:**
  - **Streamlit Web Monitoring Dashboard (`app.py`):** Real-time interactive UI for researchers and supervisors. Features research presets, custom topic inputs, direct evidence text areas, empirical value inputs, multimodal PDF uploaders, 5-stage agent status tracking, and 7-tab result inspectors.
  - **Research Report Synthesizer (`agents/research_synthesizer.py`):** Deterministic template-driven generator creating structured 5-section research abstracts in Markdown and fully compilable LaTeX (`.tex`). Enforces strict zero-hallucination number verification and overclaim filtering (`OVERCLAIM_RE`).
  - **Automated Holdout Evaluation Suite (`evaluation/`):** Evaluated across 5 scientific domains on curated holdout papers. Achieved **MRR = 1.0000**, **Recall@3 = 0.9000**, **Citation Accuracy = 100%**, and **Hallucination Rate = 0.0%**.
  - **Cost, Token & Metric Tracking (`services/cost_tracker.py`):** Real-time pipeline latency, prompt/completion token tracking, and Gemini Flash API expenditure estimation.
  - **Final Full Regression Test Suite:** **337 / 337 automated tests passing (100% Pass Rate)** across 26 test suites.

### 🌟 Week 3 Status: 100% Completed (October 30, 2026)
- **Statistical Critic Agent:** SciPy-powered hypothesis testing (`two_sample`, `paired`, `one_sample`, `multi_group`, `correlation`, `contingency`), 95% confidence intervals, and Holm-Bonferroni corrections.
- **Multimodal Gemini Vision:** Extraction of scientific charts and figures from PDFs via PyMuPDF, resolution filtering to drop icons/banners, and visual trend analysis via Google Gemini Vision.
- **Agent Memory Manager:** Sliding-window context management, token budgeting, executive summarization, and query-based relevant history retrieval.

### 🚀 Week 2 Status: 100% Completed (October 24, 2026)
- Automated detection and diagnosis of code execution errors with Gemini.
- Closed-loop bounded retry mechanism with multi-factor RL reward feedback.
- Peer-reviewed paper filtering with strict bracketed citation generation (`Evidence [N]`).
- Hardened Docker sandbox with resource quotas, non-root user isolation, and total network isolation.

### 💡 Week 1 Status: 100% Completed (October 18, 2026)
- Built core LangChain agent flow: Literature Reviewer, Hypothesis Generator, and Code Executor.
- Automated PDF text extraction (PyMuPDF) and scheduled daily GitHub Actions ingestion.
- Robust Gemini primary-to-fallback model switching (`gemini-3.8-flash` $\rightarrow$ `gemini-3.5-flash-lite`).

---

## 🏛️ System Architecture

```
                        [Scientific Literature]
                         (PubMed & ArXiv APIs)
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
         [Peer-Reviewed Filter]        [Multimodal Figure Extractor]
         (Whitelist & Metadata)        (PyMuPDF Resolution Filter)
                    │                             │
                    ▼                             ▼
        [Pinecone Vector Database]     [Gemini Vision Analyzer]
        (Gemini Embeddings: 768d)      (Trends, Axes, Labels)
                    │                             │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
              [Sequential Citation Indexer: Evidence [N]]
                                   │
                                   ▼
                       [Agent Memory Manager]
                (Sliding Window & Token Budgeting)
                                   │
                                   ▼
                      [Hypothesis Generator Agent]
                     (Grounded in Citations & Vision)
                                   │
                                   ▼
                         [Secure Docker Sandbox]
                (Resource Quotas, Read-Only, Network None)
                                   │
                                   ▼
                       [Statistical Critic Agent]
               (SciPy Tests, p-values, 95% CI, Cohen's d)
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
      [Streamlit Web Dashboard]     [Research Report Synthesizer]
    (Real-Time Monitoring UI)      (Markdown & LaTeX Abstract Export)
```

---

## 🚀 Quick Start & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/godasrinivasulureddy/autonomous-scientific-discovery-agent.git
cd autonomous-scientific-discovery-agent
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
pip install streamlit
```

### 3. Environment Configuration
Create a `.env` file in the root directory (reference [`.env.example`](.env.example)):
```ini
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=scientific-papers
```

---

## 💻 Running the Application

### Option A: Interactive Streamlit Dashboard
```cmd
streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

### Option B: Standalone Research Report Synthesis
```cmd
python -m services.demo_research_report
```
Generated reports are saved to `reports/generated/sample_report.md` and `sample_report.tex`.

### Option C: Run Holdout Evaluation Benchmark
```cmd
python -m evaluation.run_evaluation
```
Outputs benchmark metrics to `reports/evaluation/evaluation_results.json`.

---

## 🧪 Automated Testing & Verification

Run the entire test suite (337 unit, integration, and regression tests):
```bash
pytest -v -m "not live and not pinecone_live"
```

To run individual module test suites:
```bash
pytest tests/test_streamlit_app.py -v           # Streamlit UI tests
pytest tests/test_research_synthesizer.py -v     # Report synthesizer tests
pytest tests/test_evaluation_benchmark.py -v     # Evaluation benchmark tests
pytest tests/test_statistical_critic.py -v       # SciPy statistical tests
pytest tests/test_multimodal_vision.py -v        # Multimodal Gemini vision tests
pytest tests/test_docker_sandbox.py -v           # Docker security tests
```

---

## 📊 Final Evaluation Metrics (Week 4 Holdout Benchmark)

| Evaluation Metric | Benchmark Target | Achieved Result | Evaluation Verdict |
| :--- | :---: | :---: | :---: |
| **Mean Reciprocal Rank (MRR)** | $\ge 0.80$ | **1.0000** | ✅ Target Exceeded |
| **Recall@3** | $\ge 0.75$ | **0.9000** | ✅ Target Exceeded |
| **Precision@3** | $\ge 0.50$ | **0.5333** | ✅ Target Met |
| **Citation Attribution Precision** | $100\%$ | **100%** | ✅ Perfectly Grounded |
| **Hallucination Rate** | $0.0\%$ | **0.0%** | ✅ Zero Hallucinations |
| **Docker Sandbox Isolation** | $100\%$ | **100%** | ✅ Fully Hardened |
| **Automated Test Pass Rate** | $100\%$ | **337 / 337 (100%)** | ✅ All Tests Passing |

---

## ⚠️ Transparent Project Limitations

1. **AI Assistance vs. Independent Discovery:** The agent does not independently prove new scientific theories; it formulates candidate hypotheses grounded in peer-reviewed literature and verifies empirical data using standard statistical models.
2. **Human-in-the-Loop Requirement:** Synthesized research abstracts and proposed laboratory experiments require peer review and validation by qualified human domain researchers before clinical or experimental application.
3. **Template-Based Synthesis:** Research abstracts are intentionally built using deterministic templates rather than unconstrained LLM writing to mathematically prevent hallucinations and overclaiming.
