from unittest.mock import MagicMock, patch

import pytest

from services.vector_store import search_papers

def mock_embedding():
    return [0.1] * 768

def test_search_papers_can_filter_for_verified_peer_review():
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
        results = search_papers(
            "Diabetes prediction",
            top_k=3,
            peer_reviewed_only=True,
        )

    assert results == []
    mock_index.query.assert_called_once_with(
        vector=mock_embedding(),
        top_k=3,
        include_metadata=True,
        filter={"peer_review_status": {"$eq": "verified"}},
    )


def test_search_papers_default_does_not_apply_peer_review_filter():
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
        results = search_papers("Diabetes prediction")

    assert results == []
    mock_index.query.assert_called_once_with(
        vector=mock_embedding(),
        top_k=3,
        include_metadata=True,
    )


@pytest.mark.parametrize("peer_reviewed_only", [1, "true", None])
def test_search_papers_rejects_invalid_peer_reviewed_only(
    peer_reviewed_only,
):
    with pytest.raises(
        ValueError,
        match="peer_reviewed_only must be a boolean",
    ):
        search_papers(
            "Diabetes prediction",
            peer_reviewed_only=peer_reviewed_only,
        )
