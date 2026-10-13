import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict

import arxiv
import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str
    authors: list
    url: str
    published: str
    source: str  # "arxiv" or "pubmed"

    def to_dict(self):
        return asdict(self)


def build_arxiv_query(topic):
    """'machine learning drug discovery' -> all:machine AND all:learning AND ..."""
    return " AND ".join(f"all:{word}" for word in topic.split())


def search_arxiv(topic, max_results=10):
    client = arxiv.Client(page_size=max_results, delay_seconds=3, num_retries=3)
    search = arxiv.Search(
        query=build_arxiv_query(topic),
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    papers = []
    for r in client.results(search):
        papers.append(Paper(
            paper_id=f"arxiv:{r.get_short_id()}",
            title=r.title.strip(),
            abstract=r.summary.replace("\n", " ").strip(),
            authors=[a.name for a in r.authors],
            url=r.pdf_url or r.entry_id,
            published=r.published.strftime("%Y-%m-%d"),
            source="arxiv",
        ))
    return papers


def search_pubmed(topic, max_results=10):
    # Step 1: search -> list of PubMed IDs
    r = requests.get(f"{EUTILS}/esearch.fcgi", params={
        "db": "pubmed", "term": topic, "retmax": max_results,
        "retmode": "json", "sort": "date",
    }, timeout=30)
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        return []

    time.sleep(0.4)  # NCBI allows about 3 requests per second

    # Step 2: IDs -> full records (this includes the abstract)
    r = requests.get(f"{EUTILS}/efetch.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "xml",
    }, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    papers = []
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//MedlineCitation/PMID", default="")

        title_el = art.find(".//ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else "(no title)"

        abstract = " ".join(
            "".join(t.itertext()).strip() for t in art.findall(".//Abstract/AbstractText")
        )

        authors = []
        for a in art.findall(".//AuthorList/Author"):
            last, first = a.findtext("LastName"), a.findtext("ForeName")
            if last:
                authors.append(f"{first or ''} {last}".strip())

        year = art.findtext(".//JournalIssue/PubDate/Year")
        if not year:
            year = (art.findtext(".//JournalIssue/PubDate/MedlineDate") or "unknown")[:4]

        papers.append(Paper(
            paper_id=f"pubmed:{pmid}",
            title=title,
            abstract=abstract or "(no abstract available)",
            authors=authors,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            published=year,
            source="pubmed",
        ))
    return papers


def search_all(topic, max_results=10):
    """Search both sources. If one fails, still return the other."""
    papers = []
    for name, func in (("ArXiv", search_arxiv), ("PubMed", search_pubmed)):
        try:
            papers += func(topic, max_results)
        except Exception as e:
            print(f"[warning] {name} search failed: {e}")
    return papers


if __name__ == "__main__":
    for p in search_all("machine learning drug discovery", max_results=3):
        print(f"[{p.source}] {p.title}")
        print(f"   Authors:  {', '.join(p.authors[:3])}")
        print(f"   URL:      {p.url}")
        print(f"   Abstract: {p.abstract[:150]}...\n")
        