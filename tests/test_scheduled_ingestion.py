
from unittest.mock import patch

from services.paper_fetcher import Paper
from services.scheduled_ingestion import main


def make_paper(paper_id="pubmed:12345678"):
    return Paper(
        paper_id=paper_id,
        title="Scientific Discovery with Machine Learning",
        abstract="A valid scientific research abstract.",
        authors=["Test Author"],
        url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
        published="2026-10-17",
        source="pubmed",
        publication_types=["Journal Article"],
        peer_review_status="eligible_for_verification",
    )


def test_requires_peer_reviewed_filter():
    with (
        patch(
            "services.scheduled_ingestion.search_all",
            return_value=[make_paper()],
        ) as search,
        patch(
            "services.scheduled_ingestion.paper_exists",
            return_value=True,
        ),
        patch("services.scheduled_ingestion.store_paper"),
    ):
        main()

    search.assert_called_once_with(
        "machine learning drug discovery",
        max_results=2,
        peer_reviewed_only=True,
    )


def test_skips_paper_already_in_pinecone(capsys):
    paper = make_paper()

    with (
        patch(
            "services.scheduled_ingestion.search_all",
            return_value=[paper],
        ),
        patch(
            "services.scheduled_ingestion.paper_exists",
            return_value=True,
        ) as exists,
        patch(
            "services.scheduled_ingestion.store_paper",
        ) as store,
    ):
        main()

    exists.assert_called_once_with(paper.paper_id)
    store.assert_not_called()

    output = capsys.readouterr().out
    assert "already stored in Pinecone" in output
    assert "stored=0, skipped=1, failed=0" in output


def test_stores_new_paper_with_publication_metadata(capsys):
    paper = make_paper()

    with (
        patch(
            "services.scheduled_ingestion.search_all",
            return_value=[paper],
        ),
        patch(
            "services.scheduled_ingestion.paper_exists",
            return_value=False,
        ),
        patch(
            "services.scheduled_ingestion.store_paper",
            return_value={"status": "stored", "chunk_count": 1},
        ) as store,
    ):
        main()

    store.assert_called_once_with(
        paper_id=paper.paper_id,
        title=paper.title,
        text=paper.abstract,
        source=paper.source,
        url=paper.url,
        publication_types=["Journal Article"],
        peer_review_status="eligible_for_verification",
    )

    output = capsys.readouterr().out
    assert "stored=1, skipped=0, failed=0" in output


def test_skips_duplicate_search_results(capsys):
    paper = make_paper()

    with (
        patch(
            "services.scheduled_ingestion.search_all",
            return_value=[paper, paper],
        ),
        patch(
            "services.scheduled_ingestion.paper_exists",
            return_value=False,
        ),
        patch(
            "services.scheduled_ingestion.store_paper",
            return_value={"status": "stored", "chunk_count": 1},
        ) as store,
    ):
        main()

    store.assert_called_once()

    output = capsys.readouterr().out
    assert "duplicate result" in output
    assert "stored=1, skipped=1, failed=0" in output


def test_skips_missing_abstract(capsys):
    paper = make_paper()
    paper.abstract = "(no abstract available)"

    with (
        patch(
            "services.scheduled_ingestion.search_all",
            return_value=[paper],
        ),
        patch(
            "services.scheduled_ingestion.paper_exists",
        ) as exists,
        patch(
            "services.scheduled_ingestion.store_paper",
        ) as store,
    ):
        main()

    exists.assert_not_called()
    store.assert_not_called()

    output = capsys.readouterr().out
    assert "no abstract" in output
    assert "stored=0, skipped=1, failed=0" in output
