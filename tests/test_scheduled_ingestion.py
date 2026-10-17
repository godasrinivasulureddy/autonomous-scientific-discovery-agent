
from unittest.mock import patch

from services.paper_fetcher import Paper
from services.scheduled_ingestion import main


def make_paper(paper_id="arxiv:1234.5678"):
    return Paper(
        paper_id=paper_id,
        title="Scientific Discovery with Machine Learning",
        abstract="A valid scientific research abstract.",
        authors=["Test Author"],
        url="https://example.org/paper",
        published="2026-10-17",
        source="arxiv",
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


def test_stores_new_paper(capsys):
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
            return_value={
                "status": "stored",
                "chunk_count": 1,
            },
        ) as store,
    ):
        main()

    store.assert_called_once()

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
            return_value={
                "status": "stored",
                "chunk_count": 1,
            },
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
