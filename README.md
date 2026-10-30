# Autonomous Multimodal Scientific Discovery Agent

An end-to-end AI-powered autonomous scientific discovery framework that continuously ingests peer-reviewed literature, grounds research hypotheses in verifiable citations, analyzes scientific charts and figures using multimodal vision, executes empirical code inside a hardened Docker sandbox, evaluates findings using rigorous statistical tests, and maintains conversation context through intelligent memory management.

---

## 👥 Project Team

**Organization:** Zaalima Development Pvt. Ltd. (Internship Foundation)  
**Duration:** 4-Week Internship Program (October 2026)  
**Team Size:** 3 Members  

| Member | Role | Primary Modules & Responsibilities |
|---|---|---|
| **Goda Srinivasulu Reddy** | **Team Lead** | Multi-Agent Orchestration, Agent Memory Manager, Bounded Code Repair, Reward Feedback & System Integration |
| **Anand Satapara** | **Member 2** | Scientific Paper Ingestion (ArXiv/PubMed), Literature-Grounded RAG & Statistical Critic Agent (SciPy) |
| **Krishna** | **Member 3** | Pinecone Vector Database, Multimodal Gemini Vision (Figure Extraction) & Hardened Docker Sandbox |

---

## 🎯 Project Roadmap & Status

### 🏆 Week 3 Status: 100% Completed & Merged into `main` (October 30, 2026)
- **Goal:** Integrate multimodal research analysis, statistical evaluation, and improved agent memory management.
- **Key Milestones:**
  - **Statistical Critic Agent:** SciPy-powered hypothesis testing (`two_sample`, `paired`, `one_sample`, `multi_group`, `correlation`, `contingency`), 95% confidence intervals, Holm multiplicity corrections, and claim validation guards.
  - **Multimodal Gemini Vision:** Extraction of scientific charts and figures from PDFs via PyMuPDF, resolution filtering to drop icons/banners, and visual trend analysis via Google Gemini Vision.
  - **Agent Memory Manager:** Sliding-window context management, token budgeting, executive summarization, and query-based relevant history retrieval.
  - **End-to-End Multimodal Orchestration:** Unified pipeline linking literature retrieval, visual figure evidence, Docker sandbox execution, statistical critique, and persistent memory.
  - **Verification:** **282 / 282 automated tests passing (100% Pass Rate)** across 21 test suites.

### 🚀 Week 2 Status: 100% Completed & Merged (October 24, 2026)
- **Goal:** Implement literature-grounded RAG, hardened Docker execution, and an RL-based self-correcting debugging feedback loop.
- **Key Milestones:**
  - Automated detection and diagnosis of code execution errors with Gemini.
  - Closed-loop bounded retry mechanism with multi-factor RL reward feedback.
  - Peer-reviewed paper filtering with strict bracketed citation generation (`Evidence [N]`).
  - Hardened Docker sandbox with resource quotas, non-root user isolation, read-only rootfs, and total network isolation.
  - Complete integration with **221/221 unit tests passing (100%)**.

### 🌟 Week 1 Status: 100% Completed & Merged (October 18, 2026)
- **Goal:** Build the multi-agent foundation, ArXiv/PubMed ingestion pipeline, and Pinecone vector store with Gemini embeddings.
- **Key Milestones:**
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
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
           (Runtime Exception)           [Statistical Critic Agent]
                    │                    (SciPy CIs, p-values, Holm)
                    ▼                             │
        [RL Debugger & Auto-Patch]                ▼
        (Gemini Traceback Diagnosis)     [Reward Evaluation]
                    │                    (Latency, Retries, Fit)
                    └────── (Bounded Retries) ────┘
                                   │
                                   ▼
                      [Verified Discovery Report]
```

---

## 🛠️ Tech Stack & Key Technologies

- **Agent Framework:** LangChain, Python 3.11
- **LLMs & Multimodal Vision:** Google Gemini API (`gemini-3.8-flash`, `gemini-3.5-flash-lite`, `text-embedding-004`)
- **Statistical Computing:** SciPy, NumPy, Math (t-test, ANOVA, Kruskal-Wallis, Mann-Whitney U, Pearson/Spearman)
- **Scientific Sources & Processing:** NCBI PubMed API, ArXiv API, PyMuPDF (`fitz`), Pillow
- **Vector Storage:** Pinecone Vector DB (Serverless cosine index)
- **Execution & Security:** Docker (`python:3.11-slim`), Linux namespaces, cgroups, `tmpfs`, non-root execution
- **Reinforcement Learning & Memory:** Custom multi-factor reward function, sliding-window token controller
- **Testing & CI/CD:** Pytest (282 unit & integration tests), GitHub Actions

---

## 📦 Core Modules & Implemented Features

### 1. Multimodal Figure Extraction & Analysis (`services/multimodal_vision.py`)
- Automatically extracts embedded raster figures and plots from research PDFs via PyMuPDF.
- Filters out non-figure artifacts (icons, spacer bars, horizontal lines) using dimensional thresholds ($120 \times 120$ px).
- Connects to Google Gemini Vision API to extract chart types, axes labels, quantitative trends, and methodological limitations.
- Preserves full figure provenance (`figure_id`, `paper_id`, `page_number`, `reference_label`).

### 2. Statistical Critic Agent (`agents/statistical_critic.py`, `agents/experiment_evaluator.py`)
- Evaluates raw experiment numbers and stdout payloads against rigorous statistical standards.
- Supports 6 distinct experiment designs: `two_sample`, `paired`, `one_sample`, `multi_group`, `correlation`, and `contingency`.
- Calculates parametric and bootstrap 95% confidence intervals and effect sizes (Cohen's $d$, rank-biserial).
- Performs assumption checks (normality, equal variance) and enforces Holm-Bonferroni corrections for multiple tests.
- Guard functions (`check_claim`) prevent ungrounded claims of statistical significance or asserting "no difference" on non-significant p-values.

### 3. Agent Memory & Context Management (`agents/memory_manager.py`)
- Manages multi-turn conversation state with configurable token budgets (`max_tokens`) and entry caps (`max_entries`).
- Features sliding-window compression and executive background summarization to prevent context overflow.
- Enables semantic and keyword history retrieval (`retrieve_relevant_history`) to recall past findings on demand.

### 4. Literature-Grounded RAG (`agents/rag_orchestrator.py`, `services/paper_filter.py`)
- Filters papers against accredited peer-reviewed publication sources and verified PubMed IDs.
- Chunks text with overlap and stores high-dimensional semantic embeddings in Pinecone.
- Extracts citation metadata and injects indexed evidence blocks (`Evidence [1]`, `Evidence [2]`) into agent reasoning prompts to guarantee zero unsupported hallucinations.

### 5. Hardened Docker Sandbox (`services/docker_sandbox.py`)
- **Network Isolation:** `--network none` completely disables outbound/inbound network calls.
- **Read-Only Root Filesystem:** Prevents tampering or unauthorized file modification.
- **Temporary Memory Mount:** `--tmpfs /tmp:rw,noexec,nosuid,size=64m` provides in-memory scratch space without disk persistence.
- **Capability Dropping:** `--cap-drop ALL` strips all Linux root capabilities; enforced `no-new-privileges:true`.
- **Resource Constraints:** Enforces 128 MB RAM, 0.5 CPU core limit, max 64 processes (`--pids-limit 64`), and strict 30-second execution timeouts.
- **Non-Root Execution:** Runs under custom unprivileged UID/GID `10001:10001`.

### 6. RL-Based Debugging Loop (`agents/code_debugger.py`, `agents/repair_learning.py`)
- Detects runtime exceptions, syntax errors, and process timeouts.
- Parses full Python tracebacks and sends structured error context to Gemini for targeted patch generation.
- Executes self-healing retry iterations within configurable bounds (default max: 3 attempts).
- Computes multi-factor RL rewards tracking latency and retry penalties.

---

## 🧪 Testing & Quality Assurance

The codebase is protected by comprehensive unit, integration, and live container tests.

### Running Tests Locally
```bash
# Clone the repository
git clone https://github.com/godasrinivasulureddy/autonomous-scientific-discovery-agent.git
cd autonomous-scientific-discovery-agent

# Install dependencies
pip install -r requirements.txt

# Run the full test suite
pytest tests/ -v
```

### Test Suite Status
- **Total Tests:** **282 / 282 PASSED (100%)**
- **Test Modules Covered:**
  - `tests/test_statistical_critic.py` (58 tests) — SciPy hypothesis tests, Holm corrections, boundary checks
  - `tests/test_experiment_evaluator.py` (21 tests) — Executor payload adapter and JSON extraction
  - `tests/test_multimodal_vision.py` (6 tests) — PDF figure extraction, resolution filtering, Gemini Vision
  - `tests/test_memory_manager.py` (9 tests) — Sliding window, token budget, query retrieval
  - `tests/test_week3_integration.py` (6 tests) — End-to-end multi-agent, vision, critic, and memory flow
  - `tests/test_docker_sandbox.py` (13 tests) — Container isolation, timeouts, memory bounds, permissions
  - `tests/test_rag_orchestrator.py` & `tests/test_evidence.py` (24 tests) — Citation tracking, retrieval, evidence
  - `tests/test_code_debugger.py` & `tests/test_auto_repair.py` (26 tests) — Traceback diagnosis, patch synthesis
  - `tests/test_paper_ingestion.py` & `tests/test_pdf_processor.py` (29 tests) — ArXiv, PubMed, and PDF extraction
  - Additional supporting unit tests across agent and service modules (89 tests).

---

## 📚 Project Documentation & Handover Reports

| Document | Description |
|---|---|
| 📄 **[Week 3 Handover Report](reports/week3-handover.md)** | Final sign-off report detailing Week 3 deliverables across all 3 team members, full test logs, and merge audit. |
| 🚀 **[Week 3 Demo Walkthrough](docs/week3-demo.md)** | Interactive Python walkthrough covering Multimodal Vision, Memory Manager, and Statistical Critic. |
| 🏛️ **[Week 3 Architecture Specification](docs/week3-architecture.md)** | Technical specification for memory structures, SciPy critic schemas, and multimodal interfaces. |
| 📄 **[Week 2 Handover Report](reports/week2-handover.md)** | Documentation of Week 2 RAG grounding, Docker sandbox, and RL debugging feedback loop. |
| 🚀 **[Week 2 Demo Walkthrough](docs/week2-demo.md)** | Walkthrough of closed-loop code execution and bounded self-repair. |
| 🛡️ **[Week 2 Docker Security Guide](docs/week2-docker-security.md)** | Container sandboxing, security flags, resource quotas, and threat mitigation. |
| 📄 **[Week 1 Handover Report](reports/week1-handover.md)** | Documentation of Week 1 foundation, initial agent orchestration, and Pinecone setup. |
| 🚀 **[Week 1 Demo Walkthrough](docs/week1-demo.md)** | Demonstration of the baseline three-agent system and paper ingestion. |
| 📂 **[Reports Directory Index](reports/README.md)** | Central index of all project milestones, audit logs, and performance metrics. |

---

## 🔒 Security & Safe Execution Notice

- Code executed by the agent runs in an isolated container sandbox with zero network access and dropped capabilities.
- Live LLM calls and vector queries require valid environment keys (`GEMINI_API_KEY`, `PINECONE_API_KEY`).
- In case of quota exhaustion, automatic fallback switches between primary and secondary Gemini models to preserve pipeline continuity.

---

## 📄 License & Attribution

Developed under the **Zaalima Development Pvt. Ltd.** Internship Program (October 2026).  
**Repository:** [github.com/godasrinivasulureddy/autonomous-scientific-discovery-agent](https://github.com/godasrinivasulureddy/autonomous-scientific-discovery-agent)
