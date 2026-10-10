"""Download research PDFs, extract + clean their text, and save processed data."""
import json
import re
import time
from pathlib import Path

import fitz  # PyMuPDF (installed with: pip install pymupdf)
import requests

# Works whether you run it with the VS Code play button or with "python -m services.pdf_processor"
try:
    from services.paper_fetcher import Paper, search_all
except ModuleNotFoundError:
    from paper_fetcher import Paper, search_all

# Always save inside the repo's data/ folder, no matter where you run from
ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
PROCESSED_DIR = ROOT / "data" / "processed"
HEADERS = {"User-Agent": "Mozilla/5.0 (student research project)"}


def safe_name(paper_id):
    """'arxiv:2610.07997v1' -> 'arxiv_2610.07997v1' (safe to use as a filename)."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", paper_id)


# ---------- 1. Download ----------
def download_pdf(paper, retries=3):
    """Download the PDF. Only ArXiv papers have direct PDFs; PubMed returns None."""
    if paper.source != "arxiv":
        return None

    PDF_DIR.mkdir(parents=True, exist_ok=True)
    path = PDF_DIR / f"{safe_name(paper.paper_id)}.pdf"
    if path.exists() and path.stat().st_size > 0:
        return path  # already downloaded, skip

    for attempt in range(1, retries + 1):
        try:
            r = requests.get(paper.url, headers=HEADERS, timeout=60)
            r.raise_for_status()
            if "pdf" not in r.headers.get("Content-Type", "").lower():
                raise ValueError("Response is not a PDF")
            path.write_bytes(r.content)
            time.sleep(3)  # be polite to ArXiv
            return path
        except Exception as e:
            print(f"  download attempt {attempt}/{retries} failed for {paper.paper_id}: {e}")
            time.sleep(2 * attempt)
    return None


# ---------- 2. Extract ----------
def extract_text(pdf_path):
    """Return (raw_text, page_count) using PyMuPDF."""
    with fitz.open(pdf_path) as doc:
        pages = [page.get_text() for page in doc]
        return "\n".join(pages), len(pages)


# ---------- 3. Clean ----------
def clean_text(text):
    # re-join words split by a hyphen at the end of a line: "learn-\ning" -> "learning"
    text = re.sub(r"-\n(\w)", r"\1", text)
    # drop lines that contain only a page number
    text = re.sub(r"(?m)^\s*\d{1,4}\s*$", "", text)
    # cut off the References section (usually in the second half of the paper)
    matches = list(re.finditer(r"(?im)^\s*(references|bibliography)\s*$", text))
    if matches and matches[-1].start() > len(text) * 0.5:
        text = text[: matches[-1].start()]
    # keep paragraph breaks, turn single newlines into spaces
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # collapse extra spaces
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


# ---------- 4. Process one paper and save ----------
def process_paper(paper):
    """Full pipeline for one paper. Falls back to the abstract if no PDF text."""
    record = paper.to_dict()
    record.update({"text_source": "abstract", "num_pages": 0, "full_text": paper.abstract})

    pdf_path = download_pdf(paper)
    if pdf_path:
        try:
            raw, pages = extract_text(pdf_path)
            cleaned = clean_text(raw)
            if len(cleaned) > 500:  # sanity check: extraction really worked
                record.update({"text_source": "pdf", "num_pages": pages, "full_text": cleaned})
        except Exception as e:
            print(f"  extraction failed for {paper.paper_id}: {e}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / f"{safe_name(paper.paper_id)}.json"
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def run(topic, max_results=3):
    papers = search_all(topic, max_results)
    print(f"Found {len(papers)} papers for '{topic}'\n")
    results = []
    for p in papers:
        print(f"Processing {p.paper_id}: {p.title[:60]}")
        rec = process_paper(p)
        print(f"  -> source: {rec['text_source']}, {len(rec['full_text'])} characters\n")
        results.append(rec)
    return results


if __name__ == "__main__":
    run("machine learning drug discovery", max_results=3)