
from unittest.mock import MagicMock, patch

import pytest

from services.vector_store import search_papers


def mock_embedding():
    return [0.1] * 768


def test_search_papers_returns_source_metadata():
    match = MagicMock()
    match.score = 0.92
    match.metadata = {
        "paper_id": "arxiv:example",
        "chunk_number": 1,
        "title": "Diabetes Prediction Using ML",
        "text": "Machine learning can support diabetes prediction.",
        "source": "arxiv",
        "url": "https://arxiv.org/abs/example",
    }

    pinecone_results = MagicMock()
    pinecone_results.matches = [match]

    mock_index = MagicMock()
    mock_index.query.return_value = pinecone_results

    with (
        patch(
            "services.vector_store.embed_text",
            return_value=mock_embedding(),
        ),
        patch(
            "services.vector_store.get_clients",
            return_value=(MagicMock(), mock_index),
        ),
    ):
        results = search_papers("Diabetes prediction", top_k=3)

    assert len(results) == 1
    assert results[0]["paper_id"] == "arxiv:example"
    assert results[0]["title"] == "Diabetes Prediction Using ML"
    assert results[0]["text"] == (
        "Machine learning can support diabetes prediction."
    )
    assert results[0]["source"] == "arxiv"
    assert results[0]["url"] == "https://arxiv.org/abs/example"
    assert results[0]["score"] == 0.92

    mock_index.query.assert_called_once_with(
        vector=mock_embedding(),
        top_k=3,
        include_metadata=True,
    )


def test_search_papers_returns_empty_list_when_no_matches():
    pinecone_results = MagicMock()
    pinecone_results.matches = []

    mock_index = MagicMock()
    mock_index.query.return_value = pinecone_results

    with (
        patch(
            "services.vector_store.embed_text",
            return_value=mock_embedding(),
        ),
        patch(
            "services.vector_store.get_clients",
            return_value=(MagicMock(), mock_index),
        ),
    ):
        results = search_papers("Unknown research topic")

    assert results == []


@pytest.mark.parametrize("query", ["", "   ", None, 123])
def test_search_papers_rejects_invalid_query(query):
    with pytest.raises(ValueError, match="Search query cannot be empty"):
        search_papers(query)


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True, "3", None])
def test_search_papers_rejects_invalid_top_k(top_k):
    with pytest.raises(
        ValueError,
        match="top_k must be a positive integer",
    ):
        search_papers("Diabetes prediction", top_k=top_k)
