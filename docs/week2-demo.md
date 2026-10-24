# Week 2 — Scientific Discovery Agent Demo & Integration Walkthrough

**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Organization:** Zaalima Development Pvt. Ltd.  
**Team Lead:** Goda Srinivasulu Reddy  
**Team Members:** Anand Satapara, Krishna  
**Integrated Branch:** `main`  
**Final Verification Date:** October 24, 2026  

---

## 1. Overview of Week 2 Architecture

Week 2 enhances the Autonomous Multimodal Scientific Discovery Agent with a robust, production-grade closed-loop discovery cycle:

```
[Scientific Literature (ArXiv / PubMed)]
                 │
                 ▼
     [Peer-Reviewed Filter]
                 │
                 ▼
    [RAG Retrieval & Chunking] ───► [Sequential Citations: Evidence [N]]
                 │
                 ▼
   [Hypothesis Generator Agent] ───► [Literature-Grounded Hypotheses]
                 │
                 ▼
    [Docker Sandbox Execution] ───► [--network none, --read-only, --cap-drop ALL]
                 │
          (If Error / Traceback)
                 │
                 ▼
    [RL Debugger & Code Repair] ───► [Gemini Traceback Diagnosis & Auto-Patch]
                 │
                 ▼
         (Bounded Retries)
                 │
                 ▼
    [Reward Model Feedback Score] ──► [Verified Discovery Output]
```

---

## 2. Walkthrough: The 5-Stage Scientific Discovery Pipeline

### Stage 1: Peer-Reviewed Literature Ingestion & Filtering
- Ingestion fetches raw research papers from PubMed and ArXiv.
- `services/paper_filter.py` applies peer-reviewed validation rules:
  - Whitelists recognized scientific journals and verified PubMed IDs.
  - Rejects unverified, non-scientific, or low-credibility sources.
  - Extracts full metadata including DOI, authors, abstracts, and publication year.

### Stage 2: RAG Grounding & Evidence Citation
- Vector similarity search retrieves top-$k$ relevant text chunks from Pinecone.
- `services/rag_service.py` structures chunks into unambiguous evidence blocks:
  ```text
  Evidence [1]: "Recent findings show that targeting protein X inhibits viral replication in vitro." (Source: PubMed 3847291)
  Evidence [2]: "Statistical evaluation demonstrates a 35% reduction in error rates using bounded RL feedback." (Source: ArXiv 2403.11902)
  ```
- The `HypothesisGeneratorAgent` ingests this context and generates scientific hypotheses strictly grounded in and citing `Evidence [N]`.

### Stage 3: Controlled Docker Sandbox Execution
- When the hypothesis requires algorithmic validation or statistical analysis, Python code is constructed.
- The `CodeExecutorAgent` dispatches the script to `services/docker_sandbox.py`.
- **Security Configuration:**
  - Non-root user: `10001:10001`
  - Read-only root filesystem (`--read-only`) with memory-backed `/tmp` (`--tmpfs /tmp:rw,noexec,nosuid,size=64m`)
  - Full network disconnection (`--network none`)
  - Complete capability removal (`--cap-drop ALL`, `--security-opt no-new-privileges:true`)
  - Strict resource constraints: 128 MB RAM, 0.5 CPU core, maximum 64 processes (`--pids-limit 64`), 30-second execution timeout.

### Stage 4: RL Error Detection & Self-Correcting Code Repair
- If the experiment throws an unhandled exception or syntax error in the sandbox:
  - Docker captures `stdout`, `stderr`, and exit code.
  - `CodeDebuggerAgent` analyzes the traceback using Gemini prompts.
  - The debugger categorizes the failure (e.g., `IndexError`, `ZeroDivisionError`, `ImportError`), formulates a targeted patch, and logs the repair attempt.
  - The repaired code is resubmitted to the Docker sandbox within a bounded retry loop (default limit: 3 attempts).

### Stage 5: Multi-Factor RL Reward Scoring
- Once execution terminates (or exhausts retries), `agents/reward_model.py` evaluates the run:
  - **Success Reward:** Positive scalar bonus (+1.0) for valid exit code and expected data schema.
  - **Latency Penalty:** Deductions proportional to execution time.
  - **Retry Penalty:** Scaled penalty per debugging iteration to encourage rapid convergence.
  - The calculated reward and repair history are persisted for offline reinforcement learning and audit tracking.

---

## 3. End-to-End Execution Example

```python
from agents.langchain_workflow import run_scientific_discovery_pipeline

# Trigger the integrated Week 2 pipeline
result = run_scientific_discovery_pipeline(
    topic="Optimizing neural network training stability through adaptive gradient clipping",
    enable_rag=True,
    enable_docker=True,
    max_repair_retries=3
)

print("Generated Hypothesis:", result["hypothesis"])
print("Citations Found:", result["citations"])
print("Execution Status:", result["execution_result"]["status"])
print("RL Reward Score:", result["reward_score"])
print("Repair Iterations:", len(result["repair_history"]))
```

---

## 4. Verification & Validation Summary

- **Unit & Integration Tests:** 221 / 221 passing (100%).
- **Docker Sandbox Live Test:** Passed with strict resource boundaries and error handling.
- **RAG Evidence Formatting:** Fully verified with zero uncited hypothesis assertions.
- **Auto-Debugging & Retries:** Verified across syntax errors, runtime exceptions, and timeout handling.
