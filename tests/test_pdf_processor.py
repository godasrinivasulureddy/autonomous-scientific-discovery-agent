
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from services import pdf_processor


def make_paper():
    paper = Mock()
    paper.paper_id = "arxiv:2610.12345"
    paper.title = "Sample Research Paper"
    paper.source = "arxiv"
    paper.url = "https://arxiv.org/abs/2610.12345"
    paper.abstract = "Sample research abstract."
    paper.to_dict.return_value = {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "source": paper.source,
        "url": paper.url,
        "abstract": paper.abstract,
    }
    return paper


def test_safe_name_replaces_unsafe_characters():
    assert pdf_processor.safe_name("arxiv:2610/12345") == "arxiv_2610_12345"


@pytest.mark.parametrize("paper_id", ["", " ", None, 123])
def test_safe_name_rejects_invalid_paper_id(paper_id):
    with pytest.raises(ValueError, match="paper_id"):
        pdf_processor.safe_name(paper_id)


def test_download_pdf_skips_non_arxiv_papers():
    paper = make_paper()
    paper.source = "pubmed"

    assert pdf_processor.download_pdf(paper) is None


@pytest.mark.parametrize("retries", [0, -1, 1.5, True, "3", None])
def test_download_pdf_rejects_invalid_retries(retries):
    with pytest.raises(ValueError, match="retries"):
        pdf_processor.download_pdf(make_paper(), retries=retries)


def test_download_pdf_uses_existing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_processor, "PDF_DIR", tmp_path)
    paper = make_paper()
    existing_file = tmp_path / "arxiv_2610.12345.pdf"
    existing_file.write_bytes(b"%PDF-existing")

    with patch("services.pdf_processor.requests.get") as mock_get:
        result = pdf_processor.download_pdf(paper)

    assert result == existing_file
    mock_get.assert_not_called()


def test_download_pdf_rejects_non_pdf_response(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_processor, "PDF_DIR", tmp_path)
    paper = make_paper()

    response = Mock()
    response.raise_for_status.return_value = None
    response.headers = {"Content-Type": "text/html"}
    response.content = b"not a pdf"

    with (
        patch("services.pdf_processor.requests.get", return_value=response),
        patch("services.pdf_processor.time.sleep"),
    ):
        result = pdf_processor.download_pdf(paper, retries=1)

    assert result is None
    assert not (tmp_path / "arxiv_2610.12345.pdf").exists()


def test_download_pdf_retries_after_request_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_processor, "PDF_DIR", tmp_path)
    paper = make_paper()

    response = Mock()
    response.raise_for_status.return_value = None
    response.headers = {"Content-Type": "application/pdf"}
    response.content = b"%PDF-valid-content"

    with (
        patch(
            "services.pdf_processor.requests.get",
            side_effect=[pdf_processor.requests.Timeout("timeout"), response],
        ) as mock_get,
        patch("services.pdf_processor.time.sleep"),
    ):
        result = pdf_processor.download_pdf(paper, retries=2)

    assert result == tmp_path / "arxiv_2610.12345.pdf"
    assert result.read_bytes() == b"%PDF-valid-content"
    assert mock_get.call_count == 2


def test_extract_text_returns_text_and_page_count(tmp_path):
    pdf_path = tmp_path / "sample.pdf"

    with pdf_processor.pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((72, 72), "Sample PDF text.")
        document.save(pdf_path)

    text, page_count = pdf_processor.extract_text(pdf_path)

    assert "Sample PDF text." in text
    assert page_count == 1


def test_clean_text_removes_page_numbers_and_references():
    text = (
        "Introduction\n"
        "This is the main body of the research paper.\n"
        "12\n"
        "\n"
        "References\n"
        "Reference entry one\n"
        "Reference entry two\n"
    )

    cleaned = pdf_processor.clean_text(text)

    assert "Introduction" in cleaned
    assert "main body" in cleaned
    assert "12" not in cleaned
    assert "Reference entry one" not in cleaned


@pytest.mark.parametrize("text", [None, 123, []])
def test_clean_text_rejects_non_string(text):
    with pytest.raises(ValueError, match="text"):
        pdf_processor.clean_text(text)


def test_process_paper_falls_back_to_abstract(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_processor, "PROCESSED_DIR", tmp_path)
    paper = make_paper()

    with patch("services.pdf_processor.download_pdf", return_value=None):
        record = pdf_processor.process_paper(paper)

    assert record["text_source"] == "abstract"
    assert record["full_text"] == paper.abstract
    assert record["num_pages"] == 0

    saved_path = tmp_path / "arxiv_2610.12345.json"
    assert saved_path.exists()

    saved_record = json.loads(saved_path.read_text(encoding="utf-8"))
    assert saved_record == record


def test_process_paper_uses_extracted_pdf_text(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_processor, "PROCESSED_DIR", tmp_path)
    paper = make_paper()
    long_text = "Research evidence " * 50

    with (
        patch("services.pdf_processor.download_pdf", return_value=Path("sample.pdf")),
        patch(
            "services.pdf_processor.extract_text",
            return_value=(long_text, 4),
        ),
    ):
        record = pdf_processor.process_paper(paper)

    assert record["text_source"] == "pdf"
    assert record["num_pages"] == 4
    assert record["full_text"] == long_text.strip()


def test_process_paper_rejects_missing_paper_id():
    paper = make_paper()
    paper.paper_id = None

    with pytest.raises(ValueError, match="paper_id"):
        pdf_processor.process_paper(paper)


@pytest.mark.parametrize(
    ("topic", "max_results"),
    [
        ("", 3),
        ("   ", 3),
        ("valid topic", 0),
        ("valid topic", -1),
        ("valid topic", 1.5),
        ("valid topic", True),
        ("valid topic", None),
    ],
)
def test_run_rejects_invalid_inputs(topic, max_results):
    with pytest.raises(ValueError):
        pdf_processor.run(topic, max_results)


def test_run_processes_all_returned_papers():
    papers = [make_paper(), make_paper()]
    papers[1].paper_id = "arxiv:second"
    papers[1].to_dict.return_value["paper_id"] = "arxiv:second"

    with (
        patch("services.pdf_processor.search_all", return_value=papers) as mock_search,
        patch(
            "services.pdf_processor.process_paper",
            side_effect=[
                {"paper_id": papers[0].paper_id, "text_source": "abstract", "full_text": "A"},
                {"paper_id": papers[1].paper_id, "text_source": "pdf", "full_text": "B"},
            ],
        ) as mock_process,
    ):
        results = pdf_processor.run("research topic", max_results=2)

    mock_search.assert_called_once_with("research topic", 2)
    assert mock_process.call_count == 2
    assert len(results) == 2
    assert results[0]["text_source"] == "abstract"
    assert results[1]["text_source"] == "pdf"
