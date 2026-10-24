# Autonomous Multimodal Scientific Discovery Agent

An end-to-end AI-powered autonomous scientific discovery framework that continuously ingests peer-reviewed literature, grounds research hypotheses in verifiable citations, executes empirical code inside a hardened Docker sandbox, and iterates toward valid scientific solutions using reinforcement learning (RL) debugging feedback.

---

## 👥 Project Team

**Organization:** Zaalima Development Pvt. Ltd. (Internship Foundation)  
**Duration:** 4-Week Internship Program  
**Team Size:** 3 Members  

| Member | Role | Primary Modules & Responsibilities |
|---|---|---|
| **Goda Srinivasulu Reddy** | **Team Lead** | Multi-Agent Orchestration, RL Debugger, Bounded Retries, Reward Modeling & Integration |
| **Anand Satapara** | **Member 2** | Scientific Paper Ingestion (ArXiv/PubMed), Peer-Reviewed Filtering & Literature-Grounded RAG |
| **Krishna** | **Member 3** | Vector Database Storage, Secure Docker Sandbox Execution & Security Hardening |

---

## 🎯 Project Roadmap & Status

### 🚀 Week 2 Status: 100% Completed & Merged into `main` (October 24, 2026)
- **Goal:** Implement literature-grounded RAG, hardened Docker execution, and an RL-based self-correcting debugging feedback loop.
- **Key Milestones:**
  - Automated detection and diagnosis of code execution errors with Gemini.
  - Closed-loop bounded retry mechanism with multi-factor RL reward feedback.
  - Peer-reviewed paper filtering with strict bracketed citation generation (`Evidence [N]`).
  - Hardened Docker sandbox with resource quotas, non-root user isolation, read-only rootfs, and total network isolation.
  - Complete integration across all 3 modules into `main` with **221/221 unit tests passing (100%)**.

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
                                 ▼
                     [Peer-Reviewed Filter]
                    (Whitelist & Metadata)
                                 │
                                 ▼
                    [Pinecone Vector Database]
                    (Gemini Embeddings: 768d)
                                 │
                                 ▼
              [Sequential Citation Indexer: Evidence [N]]
                                 │
                                 ▼
                  [Hypothesis Generator Agent]
                 (Strictly Grounded in Evidence)
                                 │
                                 ▼
                    [Secure Docker Sandbox]
            (Resource Quotas, Read-Only, Network None)
                                 │
                                 ├───► Execution Success ──┐
                                 │                         │
                        (Runtime Exception)                │
                                 │                         ▼
                     [RL Debugger & Auto-Patch]    [Reward Evaluation]
                     (Gemini Traceback Diagnosis)  (Latency, Retries, Success)
                                 │                         │
                                 └── (Bounded Retries) ────┘
                                                           │
                                                           ▼
                                                [Verified Discovery Report]
```

---

## 🛠️ Tech Stack & Key Technologies

- **Agent Framework:** LangChain, Python 3.11
- **LLMs & Embeddings:** Google Gemini API (`gemini-3.8-flash`, `gemini-3.5-flash-lite`, `text-embedding-004`)
- **Scientific Sources:** NCBI PubMed API, ArXiv API, PyMuPDF (`fitz`)
- **Vector Storage:** Pinecone Vector DB (with ChromaDB prototype)
- **Execution & Security:** Docker (`python:3.11-slim`), Linux namespaces, cgroups, `tmpfs`, non-root execution
- **Reinforcement Learning:** Custom multi-factor reward function (success, latency, retry penalties)
- **Testing & CI/CD:** Pytest (221 unit & integration tests), GitHub Actions

---

## 📦 Core Modules & Implemented Features

### 1. Literature-Grounded RAG (`services/rag_service.py`, `services/paper_filter.py`)
- Filters papers against accredited peer-reviewed publication sources and verified PubMed IDs.
- Chunks text with overlap and stores high-dimensional semantic embeddings in Pinecone.
- Extracts citation metadata and injects indexed evidence blocks (`Evidence [1]`, `Evidence [2]`) into agent reasoning prompts to guarantee zero unsupported hallucinations.

### 2. Multi-Agent Orchestration (`agents/langchain_workflow.py`)
- **Literature Reviewer Agent:** Synthesizes research trends, methodology comparisons, and open scientific questions.
- **Hypothesis Generator Agent:** Proposes testable scientific hypotheses tied directly to retrieved literature citations.
- **Code Executor Agent:** Bridges scientific proposals to executable, reproducible statistical experiments.

### 3. Hardened Docker Sandbox (`services/docker_sandbox.py`)
- **Network Isolation:** `--network none` completely disables outbound/inbound network calls.
- **Read-Only Root Filesystem:** Prevents tampering or unauthorized file modification.
- **Temporary Memory Mount:** `--tmpfs /tmp:rw,noexec,nosuid,size=64m` provides in-memory scratch space without disk persistence.
- **Capability Dropping:** `--cap-drop ALL` strips all Linux root capabilities; enforced `no-new-privileges:true`.
- **Resource Constraints:** Enforces 128 MB RAM, 0.5 CPU core limit, max 64 processes (`--pids-limit 64`), and strict 30-second execution timeouts.
- **Non-Root Execution:** Runs under custom unprivileged UID/GID `10001:10001`.

### 4. RL-Based Debugging Loop (`agents/code_debugger.py`, `agents/reward_model.py`)
- Detects runtime exceptions, syntax errors, and process timeouts.
- Parses full Python tracebacks and sends structured error context to Gemini for targeted patch generation.
- Executes self-healing retry iterations within configurable bounds (default max: 3 attempts).
- Computes a reinforcement learning reward score:
  $$\text{Reward} = R_{\text{success}} - \lambda_{\text{time}} \cdot T - \lambda_{\text{retries}} \cdot N_{\text{retries}}$$

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
- **Total Tests:** **221 / 221 PASSED (100%)**
- **Test Modules Covered:**
  - `tests/test_docker_sandbox.py` (13 tests) — Container isolation, timeouts, memory bounds, permissions
  - `tests/test_rag_orchestrator.py` & `tests/test_rag_grounding.py` (40 tests) — Citation tracking, chunking, retrieval
  - `tests/test_code_debugger.py` & `tests/test_auto_repair.py` (26 tests) — Traceback diagnosis, patch synthesis, retry loops
  - `tests/test_langchain_workflow.py` & `tests/test_langchain_three_agents.py` (11 tests) — End-to-end agent orchestration
  - `tests/test_paper_ingestion.py` & `tests/test_pdf_processor.py` (53 tests) — ArXiv, PubMed, and PDF extraction
  - Additional unit tests covering vector stores, Gemini fallback, and scheduled pipelines (78 tests).

### GitHub Actions CI/CD Workflows
- **Docker Sandbox Live Test:** Verified on cloud runners with real Docker daemon (`sandbox/Dockerfile`).
- **Python Tests Workflow:** Automated regression suite running on every pull request and push to `main`.
- **Scheduled Ingestion Workflow:** Automated daily cron (03:00 UTC) fetching fresh literature into Pinecone.

---

## 📚 Project Documentation & Handover Reports

| Document | Description |
|---|---|
| 📄 **[Week 2 Handover Report](reports/week2-handover.md)** | Final sign-off report detailing Week 2 day-wise deliverables, member contributions, test logs, and merge audit. |
| 🚀 **[Week 2 Demo Walkthrough](docs/week2-demo.md)** | Step-by-step visual and architectural walkthrough of the closed-loop discovery pipeline. |
| 🛡️ **[Week 2 Docker Security Guide](docs/week2-docker-security.md)** | Deep dive into container sandboxing, security flags, resource quotas, and threat mitigation. |
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
