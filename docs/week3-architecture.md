# Week 3 — Architecture & Interface Specification

**Project:** Autonomous Multimodal Scientific Discovery Agent  
**Company:** Zaalima Development Pvt. Ltd.  
**Author:** Goda Srinivasulu Reddy (Team Lead)  
**Date:** 23 October 2026 (Day 1)  
**Branch:** `feature/week3-memory-integration`  

---

## 1. Objectives

Week 3 enhances the scientific discovery pipeline with:
1. **Multimodal Analysis (Gemini Vision)**: Extracting and reasoning about charts and figures from scientific PDFs.
2. **Statistical Critic Agent**: Rigorous statistical tests ($t$-test, ANOVA, Mann-Whitney, confidence intervals, $p$-values) evaluating experimental hypotheses and outputs.
3. **Context-Window & Agent Memory Management**: Rolling context compression, memory summarization, and token budgeting preventing context overflow and drift.

---

## 2. Component Architecture & Workflow

```
[Scientific PDF / Papers]
        │
        ├──► Text Ingestion ──► Vector RAG ──► Literature Review
        │                                             │
        └──► Vision Extraction ──► Gemini Vision ─────┤
             (Charts & Figures)   (Visual Trends)     ▼
                                            [Hypothesis Generator]
                                            (Grounded in Citations & Visuals)
                                                      │
                                                      ▼
                                            [Code Executor (Docker)]
                                            (Standardized Result Output)
                                                      │
                                                      ▼
                                            [Statistical Critic Agent]
                                            (p-value, CI, Hypothesis Evaluation)
                                                      │
                                                      ▼
                                            [Agent Memory Manager]
                                            (Sliding Window, History, Summary)
```

---

## 3. Module Interface Specifications

### 3.1 Code Executor & Experiment Results Interface
Standardized dictionary representation returned by `agents/code_executor.py`:

```json
{
  "experiment": "descriptive_statistics" | "two_sample_t_test" | "custom_statistical_test",
  "status": "success" | "error" | "skipped",
  "data": {
    "sample_size": 100,
    "metrics": {
      "mean": 12.4,
      "standard_deviation": 1.8
    },
    "raw_values": [12.1, 12.5, ...]
  },
  "metadata": {
    "execution_time_seconds": 0.42,
    "docker_sandboxed": true,
    "timestamp": "2026-10-24T12:00:00Z"
  },
  "error": null
}
```

### 3.2 Statistical Critic Agent Interface
Input and output schema for Member 2 (Anand)'s `Statistical Critic Agent`:

**Input:**
```python
{
    "hypothesis": str,
    "experiment_result": dict, # Conforming to 3.1
    "alpha": float,            # Default 0.05
    "test_type": str           # e.g., "t_test", "mann_whitney", "descriptive"
}
```

**Output:**
```python
{
    "status": "evaluated" | "inconclusive" | "failed",
    "test_name": str,
    "p_value": float | None,
    "confidence_interval": [float, float] | None,
    "significant": bool,
    "assumptions_met": bool,
    "criticism": str,
    "recommendations": list[str]
}
```

### 3.3 Gemini Vision Interface
Input and output schema for Member 3 (Krishna)'s `Gemini Vision` module:

**Input:**
```python
{
    "paper_id": str,
    "figure_id": str,
    "image_bytes": bytes | str,  # Raw bytes or image path
    "caption": str | None
}
```

**Output:**
```python
{
    "paper_id": str,
    "figure_id": str,
    "chart_type": "bar" | "scatter" | "line" | "heatmap" | "other",
    "trends": list[str],
    "extracted_labels": list[str],
    "visual_summary": str
}
```

### 3.4 Context-Window & Memory Management Interface
Managed by `agents/memory_manager.py` (Team Lead):

```python
class AgentMemoryManager:
    def __init__(self, max_tokens: int = 4000, max_entries: int = 10):
        ...
    def add_interaction(self, role: str, content: str, metadata: dict | None = None) -> None:
        ...
    def get_context(self) -> str:
        ...
    def summarize_older_context(self) -> str:
        ...
    def clear(self) -> None:
        ...
```

---

## 4. Work Distribution & Milestones

| Member | Focus | Deliverables |
|---|---|---|
| **Goda Srinivasulu Reddy (Lead)** | Memory & Orchestrator | `memory_manager.py`, standardized code executor metadata, integrated pipeline |
| **Anand Satapara** | Statistical Critic | `statistical_critic.py`, SciPy hypothesis tests, significance checks |
| **Krishna** | Multimodal Vision | `vision_service.py`, chart extraction, visual trend summarization |
