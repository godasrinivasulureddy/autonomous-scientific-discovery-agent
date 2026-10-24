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



from services.paper_fetcher import _is_eligible_pubmed_article


def test_peer_review_filter_rejects_preprints():
    assert _is_eligible_pubmed_article(["Preprint"]) is False


def test_peer_review_filter_rejects_editorials():
    assert _is_eligible_pubmed_article(["Editorial"]) is False


def test_peer_review_filter_rejects_missing_publication_types():
    assert _is_eligible_pubmed_article([]) is False


def test_peer_review_filter_accepts_research_article_for_verification():
    assert _is_eligible_pubmed_article(["Journal Article"]) is True




from unittest.mock import Mock, patch

from services.paper_fetcher import search_pubmed


def make_pubmed_xml(publication_types, pmid="12345"):
    types_xml = "".join(
        f"<PublicationType>{value}</PublicationType>"
        for value in publication_types
    )
    return f"""
    <PubmedArticleSet>
      <PubmedArticle>
        <MedlineCitation>
          <PMID>{pmid}</PMID>
          <Article>
            <Journal>
              <JournalIssue>
                <PubDate><Year>2025</Year></PubDate>
              </JournalIssue>
            </Journal>
            <ArticleTitle>Test Research Paper</ArticleTitle>
            <Abstract>
              <AbstractText>Test abstract.</AbstractText>
            </Abstract>
            <AuthorList>
              <Author>
                <ForeName>Jane</ForeName>
                <LastName>Smith</LastName>
              </Author>
            </AuthorList>
            <PublicationTypeList>{types_xml}</PublicationTypeList>
          </Article>
        </MedlineCitation>
      </PubmedArticle>
    </PubmedArticleSet>
    """.encode()


def mock_pubmed_responses(xml_content):
    search_response = Mock()
    search_response.json.return_value = {
        "esearchresult": {"idlist": ["12345"]}
    }
    search_response.raise_for_status.return_value = None

    fetch_response = Mock()
    fetch_response.content = xml_content
    fetch_response.raise_for_status.return_value = None

    return [search_response, fetch_response]


@patch("services.paper_fetcher.time.sleep")
@patch("services.paper_fetcher.requests.get")
def test_search_pubmed_filters_preprints_when_requested(
    mock_get, mock_sleep
):
    mock_get.side_effect = mock_pubmed_responses(
        make_pubmed_xml(["Preprint"])
    )

    papers = search_pubmed(
        "machine learning",
        peer_reviewed_only=True,
    )

    assert papers == []


@patch("services.paper_fetcher.time.sleep")
@patch("services.paper_fetcher.requests.get")
def test_search_pubmed_returns_eligible_article_metadata(
    mock_get, mock_sleep
):
    mock_get.side_effect = mock_pubmed_responses(
        make_pubmed_xml(["Journal Article"])
    )

    papers = search_pubmed(
        "machine learning",
        peer_reviewed_only=True,
    )

    assert len(papers) == 1
    assert papers[0].paper_id == "pubmed:12345"
    assert papers[0].title == "Test Research Paper"
    assert papers[0].authors == ["Jane Smith"]
    assert papers[0].publication_types == ["Journal Article"]
    assert papers[0].peer_review_status == "eligible_for_verification"




def test_ingestion_requests_peer_review_eligible_papers():
    paper = make_paper("pubmed:12345")
    paper.publication_types = ["Journal Article"]
    paper.peer_review_status = "eligible_for_verification"

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper],
        ) as mock_search,
        patch("services.vector_store.paper_exists", return_value=True),
        patch("services.vector_store.store_paper") as mock_store,
    ):
        result = ingest_research_papers("machine learning", max_results=2)

    mock_search.assert_called_once_with(
        "machine learning",
        max_results=2,
        peer_reviewed_only=True,
    )
    mock_store.assert_not_called()
    assert result["status"] == "completed"
    assert result["skipped_papers"] == ["pubmed:12345"]


def test_ingestion_stores_publication_metadata():
    paper = make_paper("pubmed:12345")
    paper.publication_types = ["Journal Article"]
    paper.peer_review_status = "eligible_for_verification"

    record = make_record(
        title="PubMed Research",
        source="pubmed",
        url="https://pubmed.ncbi.nlm.nih.gov/12345/",
        full_text="Full text of the research paper.",
    )

    with (
        patch(
            "services.paper_fetcher.search_all",
            return_value=[paper],
        ),
        patch("services.vector_store.paper_exists", return_value=False),
        patch(
            "services.pdf_processor.process_paper",
            return_value=record,
        ),
        patch(
            "services.vector_store.store_paper",
            return_value={"status": "stored", "chunk_count": 1},
        ) as mock_store,
    ):
        result = ingest_research_papers("machine learning", max_results=1)

    mock_store.assert_called_once_with(
        paper_id="pubmed:12345",
        title="PubMed Research",
        text="Full text of the research paper.",
        source="pubmed",
        url="https://pubmed.ncbi.nlm.nih.gov/12345/",
        publication_types=["Journal Article"],
        peer_review_status="eligible_for_verification",
    )

    assert result["status"] == "completed"
    assert result["paper_count"] == 1

