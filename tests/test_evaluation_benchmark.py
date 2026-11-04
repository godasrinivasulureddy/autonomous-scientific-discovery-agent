"""Unit and integration tests for the evaluation suite (Krishna - Week 4)."""

import pytest
from evaluation.evaluator import (
    compute_precision_at_k,
    compute_recall_at_k,
    compute_mrr,
    verify_citation_grounding,
    evaluate_retrieval_benchmark,
)


def test_compute_precision_and_recall_at_k():
    retrieved = ["doc1", "doc2", "doc3", "doc4"]
    relevant = {"doc1", "doc3", "doc5"}

    # Top 2: retrieved doc1 (relevant), doc2 (not) -> P@2 = 1/2 = 0.5
    assert compute_precision_at_k(retrieved, relevant, k=2) == 0.5

    # Top 4: retrieved doc1, doc3 -> P@4 = 2/4 = 0.5
    assert compute_precision_at_k(retrieved, relevant, k=4) == 0.5

    # Recall at 2: 1 / 3 relevant docs = 0.3333
    assert compute_recall_at_k(retrieved, relevant, k=2) == 0.3333

    # Recall at 4: 2 / 3 relevant docs = 0.6667
    assert compute_recall_at_k(retrieved, relevant, k=4) == 0.6667


def test_compute_mrr():
    relevant = {"target_doc"}

    # First position rank 1 -> RR = 1.0
    assert compute_mrr(["target_doc", "other"], relevant) == 1.0

    # Second position rank 2 -> RR = 0.5
    assert compute_mrr(["other", "target_doc"], relevant) == 0.5

    # Third position rank 3 -> RR = 0.3333
    assert compute_mrr(["other1", "other2", "target_doc"], relevant) == 0.3333

    # Not found -> RR = 0.0
    assert compute_mrr(["other1", "other2"], relevant) == 0.0


def test_verify_citation_grounding_valid():
    hypo = "Based on evidence [1] and [2], Cas9 mutations decrease off-target effects."
    available = [1, 2, 3]
    res = verify_citation_grounding(hypo, available)
    assert res["is_fully_grounded"] is True
    assert res["total_citations"] == 2
    assert res["invalid_citations"] == []


def test_verify_citation_grounding_invalid():
    hypo = "Based on evidence [1] and hallucinated claim [9], Cas9 improves."
    available = [1, 2]
    res = verify_citation_grounding(hypo, available)
    assert res["is_fully_grounded"] is False
    assert res["invalid_citations"] == [9]


def test_evaluate_retrieval_benchmark_mock(tmp_path):
    dataset_file = tmp_path / "test_dataset.json"
    dataset_file.write_text(
        """[
            {"query_id": "T1", "query": "test query", "relevant_doc_ids": ["doc_A"]}
        ]""",
        encoding="utf-8",
    )

    def mock_retriever(query, top_k=3):
        return [{"id": "doc_A"}, {"id": "doc_B"}]

    benchmark = evaluate_retrieval_benchmark(dataset_file, mock_retriever, top_k=2)
    assert benchmark["queries_evaluated"] == 1
    assert benchmark["mean_precision_at_k"] == 0.5
    assert benchmark["mean_recall_at_k"] == 1.0
    assert benchmark["mean_mrr"] == 1.0
