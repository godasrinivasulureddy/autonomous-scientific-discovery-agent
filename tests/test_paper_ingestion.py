
from unittest.mock import MagicMock, patch

from agents.orchestrator import ingest_research_papers


def test_paper_ingestion():
    paper = MagicMock()
    paper.paper_id = "arxiv:12345"

    processed_record = {
        "title": "Machine Learning Research",
        "source": "arxiv",
        "url": "https://arxiv.org/abs/12345",
        "full_text": "Scientific research about machine learning.",
    }

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper],
        ),
        patch(
            "services.pdf_processor.process_paper",
            return_value=processed_record,
        ),
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
    paper = MagicMock()
    paper.paper_id = "arxiv:12345"

    record = {
        "title": "Sample Research",
        "source": "arxiv",
        "url": "https://arxiv.org/abs/12345",
        "full_text": "Research paper content.",
    }

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper, paper],
        ),
        patch(
            "services.pdf_processor.process_paper",
            return_value=record,
        ),
        patch("services.vector_store.store_paper") as mock_store,
    ):
        result = ingest_research_papers("machine learning")

    assert result["paper_count"] == 1
    mock_store.assert_called_once()


def test_empty_paper_not_stored():
    paper = MagicMock()
    paper.paper_id = "arxiv:empty"

    record = {
        "title": "Empty Paper",
        "source": "arxiv",
        "url": "",
        "full_text": "   ",
    }

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper],
        ),
        patch(
            "services.pdf_processor.process_paper",
            return_value=record,
        ),
        patch("services.vector_store.store_paper") as mock_store,
    ):
        result = ingest_research_papers("machine learning")

    assert result["paper_count"] == 0
    mock_store.assert_not_called()

