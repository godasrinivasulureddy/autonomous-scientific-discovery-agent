"""
Automated Evaluation Suite for Retrieval, Citation Grounding, and Experiment Execution.
Author: Krishna (Testing & Evaluation)
Organization: Zaalima Development Pvt. Ltd. (Week 4)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set
import re


def compute_precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """Compute Precision@k."""
    if k <= 0 or not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return round(hits / float(k), 4)


def compute_recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """Compute Recall@k."""
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return round(hits / float(len(relevant_ids)), 4)


def compute_mrr(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    """Compute Reciprocal Rank of first relevant retrieved document."""
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return round(1.0 / rank, 4)
    return 0.0


def verify_citation_grounding(hypothesis_text: str, available_evidence_ids: List[int]) -> Dict[str, Any]:
    """Verify that every citation in hypothesis maps to available evidence IDs."""
    citation_pattern = re.compile(r"\[(\d+)\]")
    matches = citation_pattern.findall(hypothesis_text)
    cited_ids = [int(m) for m in matches]

    valid_ids = set(available_evidence_ids)
    invalid_citations = [cid for cid in cited_ids if cid not in valid_ids]

    return {
        "total_citations": len(cited_ids),
        "valid_citations": len(cited_ids) - len(invalid_citations),
        "invalid_citations": invalid_citations,
        "is_fully_grounded": len(invalid_citations) == 0 and len(cited_ids) > 0,
    }


def evaluate_retrieval_benchmark(
    dataset_path: str | Path,
    retrieval_function: Any,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Run batch retrieval evaluation across all holdout questions."""
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Holdout dataset not found at {path}")

    with open(path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    results = []
    p_at_k_scores = []
    r_at_k_scores = []
    mrr_scores = []

    for item in cases:
        query = item["query"]
        relevant = set(item["relevant_doc_ids"])

        retrieved_docs = retrieval_function(query, top_k=top_k)
        retrieved_ids = [doc.get("id", doc.get("doc_id", f"doc_{i}")) for i, doc in enumerate(retrieved_docs)]

        p_k = compute_precision_at_k(retrieved_ids, relevant, k=top_k)
        r_k = compute_recall_at_k(retrieved_ids, relevant, k=top_k)
        mrr = compute_mrr(retrieved_ids, relevant)

        p_at_k_scores.append(p_k)
        r_at_k_scores.append(r_k)
        mrr_scores.append(mrr)

        results.append({
            "query_id": item["query_id"],
            "query": query,
            "precision_at_k": p_k,
            "recall_at_k": r_k,
            "mrr": mrr,
        })

    avg_p_k = round(sum(p_at_k_scores) / len(p_at_k_scores), 4) if p_at_k_scores else 0.0
    avg_r_k = round(sum(r_at_k_scores) / len(r_at_k_scores), 4) if r_at_k_scores else 0.0
    avg_mrr = round(sum(mrr_scores) / len(mrr_scores), 4) if mrr_scores else 0.0

    return {
        "queries_evaluated": len(cases),
        "top_k": top_k,
        "mean_precision_at_k": avg_p_k,
        "mean_recall_at_k": avg_r_k,
        "mean_mrr": avg_mrr,
        "detailed_results": results,
    }
