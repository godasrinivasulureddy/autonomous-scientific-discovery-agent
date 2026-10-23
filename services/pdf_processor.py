"""Download research PDFs, extract and clean text, and save processed data."""

import json
import re
import time
from pathlib import Path

import pymupdf
import requests

try:
    from services.paper_fetcher import Paper, search_all
except ModuleNotFoundError:
    from paper_fetcher import Paper, search_all


ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
PROCESSED_DIR = ROOT / "data" / "processed"
HEADERS = {"User-Agent": "ScientificDiscoveryAgent/1.0 (research project)"}


def safe_name(paper_id):
    """Convert a paper ID into a safe filename."""
    if not isinstance(paper_id, str) or not paper_id.strip():
        raise ValueError("paper_id must be a non-empty string")
    return re.sub(r"[^A-Za-z0-9._-]", "_", paper_id)


def download_pdf(paper, retries=3):
    """Download an ArXiv PDF; return None when unavailable."""
    if paper.source != "arxiv":
        return None

    if type(retries) is not int or retries < 1:
        raise ValueError("retries must be a positive integer")

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    filename = safe_name(paper.paper_id)
    path = PDF_DIR / f"{filename}.pdf"

    if path.exists() and path.stat().st_size > 0:
        return path

    pdf_url = f"https://arxiv.org/pdf/{paper.paper_id.split(':')[-1]}"
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(
                pdf_url,
                headers=HEADERS,
                timeout=60,
            )
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            if "pdf" not in content_type or not response.content.startswith(b"%PDF"):
                raise ValueError("Response is not a valid PDF")

            path.write_bytes(response.content)
            time.sleep(3)
            return path

        except (requests.RequestException, OSError, ValueError) as exc:
            last_error = exc
            print(
                f"Download attempt {attempt}/{retries} failed "
                f"for {paper.paper_id}: {exc}"
            )
            if attempt < retries:
                time.sleep(2 * attempt)

    print(f"PDF download failed for {paper.paper_id}: {last_error}")
    return None


def extract_text(pdf_path):
    """Return extracted PDF text and page count."""
    with pymupdf.open(pdf_path) as document:
        pages = [page.get_text() for page in document]
        return "\n".join(pages), len(pages)


def clean_text(text):
    """Normalize extracted text and remove a detected references section."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")

    text = re.sub(r"-\s*\n(\w)", r"\1", text)
    text = re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)

    headings = list(
        re.finditer(
            r"(?im)^\s*(references|bibliography)\s*$",
            text,
        )
    )
    if headings:
        heading = headings[-1]
        if heading.start() > len(text) * 0.5:
            text = text[:heading.start()]

    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def process_paper(paper):
    """Process one paper, using its abstract if PDF extraction is unavailable."""
    if not getattr(paper, "paper_id", None):
        raise ValueError("Paper must have a valid paper_id")

    record = paper.to_dict()
    abstract = getattr(paper, "abstract", "") or ""

    record.update(
        {
            "text_source": "abstract",
            "num_pages": 0,
            "full_text": abstract,
        }
    )

    pdf_path = download_pdf(paper)

    if pdf_path is not None:
        try:
            raw_text, page_count = extract_text(pdf_path)
            cleaned_text = clean_text(raw_text)

            if len(cleaned_text) > 500:
                record.update(
                    {
                        "text_source": "pdf",
                        "num_pages": page_count,
                        "full_text": cleaned_text,
                    }
                )
        except (OSError, ValueError, RuntimeError) as exc:
            print(f"PDF extraction failed for {paper.paper_id}: {exc}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / f"{safe_name(paper.paper_id)}.json"
    output_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return record


def run(topic, max_results=3):
    """Fetch and process research papers for a topic."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("topic must be a non-empty string")
    if type(max_results) is not int or max_results < 1:
        raise ValueError("max_results must be a positive integer")

    papers = search_all(topic.strip(), max_results)
    print(f"Found {len(papers)} papers for '{topic.strip()}'\n")

    results = []
    for paper in papers:
        print(f"Processing {paper.paper_id}: {paper.title[:60]}")
        record = process_paper(paper)
        print(
            f"  -> source: {record['text_source']}, "
            f"{len(record['full_text'])} characters\n"
        )
        results.append(record)

    return results


if __name__ == "__main__":
    run("machine learning drug discovery", max_results=3)
