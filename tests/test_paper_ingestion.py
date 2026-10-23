from unittest.mock import MagicMock, patch

import pytest

from agents.orchestrator import ingest_research_papers


def make_paper(paper_id="arxiv:12345"):
    paper = MagicMock()
    paper.paper_id = paper_id
    return paper


def make_record(
    title="Machine Learning Research",
    source="arxiv",
    url="https://arxiv.org/abs/12345",
    full_text="Scientific research about machine learning.",
):
    return {
        "title": title,
        "source": source,
        "url": url,
        "full_text": full_text,
    }


def test_paper_ingestion():
    paper = make_paper()
    record = make_record()

    with (
        patch("services.paper_fetcher.search_all", return_value=[paper]),
        patch("services.pdf_processor.process_paper", return_value=record),
        patch(
            "services.vector_store.store_paper",
            return_value={
                "status": "stored",
                "paper_id": "arxiv:12345",
                "chunk_count": 1,
            },
        ) as mock_store,
    ):
        result = ingest_research_papers(
            research_topic="machine learning",
            max_results=1,
        )

    assert result["paper_count"] == 1
    assert result["stored_papers"][0]["status"] == "stored"

    mock_store.assert_called_once_with(
        paper_id="arxiv:12345",
        title="Machine Learning Research",
        text="Scientific research about machine learning.",
        source="arxiv",
        url="https://arxiv.org/abs/12345",
    )


def test_duplicate_papers_stored_once():
    paper = make_paper()
    record = make_record(
        title="Sample Research",
        url="https://arxiv.org/abs/12345",
        full_text="Research paper content.",
    )

    with (
        patch("services.paper_fetcher.search_all", return_value=[paper, paper]),
        patch("services.pdf_processor.process_paper", return_value=record),
        patch(
            "services.vector_store.store_paper",
            return_value={"status": "stored"},
        ) as mock_store,
    ):
        result = ingest_research_papers("machine learning")

    assert result["paper_count"] == 1
    mock_store.assert_called_once()


def test_empty_paper_not_stored():
    paper = make_paper("arxiv:empty")
    record = make_record(
        title="Empty Paper",
        url="",
        full_text="   ",
    )

    with (
        patch("services.paper_fetcher.search_all", return_value=[paper]),
        patch("services.pdf_processor.process_paper", return_value=record),
        patch("services.vector_store.store_paper") as mock_store,
    ):
        result = ingest_research_papers("machine learning")

    assert result["paper_count"] == 0
    mock_store.assert_not_called()


@pytest.mark.parametrize(
    "topic",
    ["", "   ", None, 123],
)
def test_invalid_topic_rejected(topic):
    with pytest.raises((ValueError, TypeError)):
        ingest_research_papers(topic)


@pytest.mark.parametrize(
    "max_results",
    [0, -1, 1.5, True, "3", None],
)
def test_invalid_max_results_rejected(max_results):
    with pytest.raises((ValueError, TypeError)):
        ingest_research_papers(
            "machine learning",
            max_results=max_results,
        )


def test_paper_without_id_is_not_stored():
    paper = make_paper("")
    record = make_record()

    with (
        patch("services.paper_fetcher.search_all", return_value=[paper]),
        patch("services.pdf_processor.process_paper", return_value=record),
        patch("services.vector_store.store_paper") as mock_store,
    ):
        result = ingest_research_papers("machine learning")

    assert result["paper_count"] == 0
    mock_store.assert_not_called()
