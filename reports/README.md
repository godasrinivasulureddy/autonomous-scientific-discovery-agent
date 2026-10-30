# Project Reports & Documentation Index

**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Organization:** Zaalima Development Pvt. Ltd. (Internship Foundation)  
**Lead:** Goda Srinivasulu Reddy | **Members:** Anand Satapara, Krishna  

This folder contains formal milestone handover reports, technical documentation, testing evidence, and project audit records across Weeks 1, 2, and 3.

---

## 📑 Milestone Handover Reports

| Milestone | Report Link | Primary Deliverables | Test Suite Status |
|---|---|---|:---:|
| **Week 3 Handover** | 📄 [Week 3 Development Handover Report](week3-handover.md) | Multimodal Vision (PDF figure extraction), Statistical Critic Agent (SciPy hypothesis testing, CIs, Holm correction), Agent Memory Manager (sliding window, token budget), and end-to-end integration. | **282 / 282 Passed (100%)** |
| **Week 2 Handover** | 📄 [Week 2 Development Handover Report](week2-handover.md) | Peer-reviewed RAG literature grounding (`Evidence [N]` citations), zero-trust Docker execution sandbox, and Gemini-assisted self-healing code repair loop with RL reward model. | **221 / 221 Passed (100%)** |
| **Week 1 Handover** | 📄 [Week 1 Development Handover Report](week1-handover.md) | Multi-agent research foundation (Literature Reviewer, Hypothesis Generator, Code Executor), PubMed/ArXiv paper ingestion, and Pinecone vector store with Gemini embeddings. | **80+ Passed (100%)** |

---

## 🚀 Interactive Walkthroughs & Architecture Guides

- 🏛️ **[Week 3 Architecture Specification](../docs/week3-architecture.md):** Formal interface specifications for Multimodal Gemini Vision, Statistical Critic JSON payloads, and Memory Manager token budgeting.
- 🚀 **[Week 3 Demo Walkthrough](../docs/week3-demo.md):** Python walkthrough showing multimodal figure extraction, context memory retention, and statistical evaluation.
- 🛡️ **[Week 2 Docker Security Guide](../docs/week2-docker-security.md):** Deep technical dive into container hardening (`--network none`, `--read-only`, `--cap-drop ALL`, resource caps, non-root execution).
- 🚀 **[Week 2 Demo Walkthrough](../docs/week2-demo.md):** Complete walkthrough of the closed-loop self-repair and RAG-grounded discovery workflow.
- 🚀 **[Week 1 Demo Walkthrough](../docs/week1-demo.md):** Overview of initial multi-agent coordination and paper ingestion.

---

## 👥 Implementation Status by Workstream

### 1. Agent Memory & System Orchestration (Goda Srinivasulu Reddy — Team Lead)
- **Agent Memory Manager (`agents/memory_manager.py`):** Sliding window history retention, token counter budgeting, executive summarization, and query-based relevant history retrieval.
- **Unified Multimodal Orchestration (`agents/orchestrator.py`):** `run_multimodal_research_pipeline` and `run_research_workflow` connecting literature, visual figure evidence, Docker sandbox, and Statistical Critic.
- **Reinforcement Learning Auto-Repair (`agents/code_debugger.py`, `agents/repair_learning.py`):** Closed-loop error diagnosis, AST validation, bounded retries (max 3), and multi-factor RL reward scoring.

### 2. Statistical Critic & Literature-Grounded RAG (Anand Satapara — Member 2)
- **Statistical Critic Agent (`agents/statistical_critic.py`):** SciPy parametric and non-parametric tests (`two_sample`, `paired`, `one_sample`, `multi_group`, `correlation`, `contingency`), 95% confidence intervals, Holm multiplicity corrections, and claim validation guards.
- **Experiment Evaluator Adapter (`agents/experiment_evaluator.py`):** Adapts executor dictionaries and stdout JSON into structured statistical criticism.
- **Peer-Reviewed RAG (`agents/rag_orchestrator.py`, `services/paper_filter.py`):** Verified publication source filtering, Pinecone semantic retrieval, and bracketed `Evidence [N]` sequential citation mapping.

### 3. Multimodal Vision & Docker Sandbox Security (Krishna — Member 3)
- **Multimodal Figure Extraction & Analysis (`services/multimodal_vision.py`):** PyMuPDF image stream extraction, resolution artifact filtering ($120 \times 120$ px threshold), and Google Gemini Vision structured analysis.
- **Hardened Docker Sandbox (`services/docker_sandbox.py`):** Cgroups and namespace isolation (`--network none`, `--read-only`, non-root user `10001:10001`, 128MB RAM, 0.5 CPU, 64 PIDs, and 30s timeout).
- **Pinecone Vector Database (`services/vector_store.py`):** Chunking with overlap, Gemini 768-dimensional embeddings, and duplicate paper deduplication.

---

## 📊 Comprehensive Test Suite Summary

- **Total Test Cases:** **282**
- **Passing:** **282 (100%)**
- **Failures / Errors:** **0**
- **Verification Environment:** Pytest 8.3, Python 3.11, Windows x64 & GitHub Actions Linux Runner.
