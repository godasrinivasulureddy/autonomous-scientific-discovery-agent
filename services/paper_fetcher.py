import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass

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
    source: str
    publication_types: list = None

    def to_dict(self):
        return asdict(self)


def build_arxiv_query(topic):
    """Convert a topic into an ArXiv all-fields query."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    words = topic.split()
    return " AND ".join(f"all:{word}" for word in words)


def search_arxiv(topic, max_results=10):
    """Search ArXiv and return structured paper metadata."""
    if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results < 1:
        raise ValueError("max_results must be a positive integer.")

    client = arxiv.Client(
        page_size=max_results,
        delay_seconds=3,
        num_retries=3,
    )
    search = arxiv.Search(
        query=build_arxiv_query(topic),
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    papers = []
    for result in client.results(search):
        papers.append(
            Paper(
                paper_id=f"arxiv:{result.get_short_id()}",
                title=result.title.strip(),
                abstract=result.summary.replace("\n", " ").strip(),
                authors=[author.name for author in result.authors],
                url=result.pdf_url or result.entry_id,
                published=result.published.strftime("%Y-%m-%d"),
                source="arxiv",
            )
        )

    return papers


def search_pubmed(topic, max_results=10):
    """Search PubMed and return structured paper metadata."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results < 1:
        raise ValueError("max_results must be a positive integer.")

    response = requests.get(
        f"{EUTILS}/esearch.fcgi",
        params={
            "db": "pubmed",
            "term": topic,
            "retmax": max_results,
            "retmode": "json",
            "sort": "date",
        },
        timeout=30,
    )
    response.raise_for_status()

    ids = response.json()["esearchresult"]["idlist"]
    if not ids:
        return []

    time.sleep(0.4)

    response = requests.get(
        f"{EUTILS}/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "xml",
        },
        timeout=30,
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    papers = []

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID", default="").strip()
        if not pmid:
            continue

        title_element = article.find(".//ArticleTitle")
        title = (
            "".join(title_element.itertext()).strip()
            if title_element is not None
            else "(no title)"
        )

        abstract = " ".join(
            "".join(element.itertext()).strip()
            for element in article.findall(".//Abstract/AbstractText")
        ).strip()

        authors = []
        for author in article.findall(".//AuthorList/Author"):
            last_name = author.findtext("LastName")
            first_name = author.findtext("ForeName")
            if last_name:
                authors.append(f"{first_name or ''} {last_name}".strip())

        year = article.findtext(".//JournalIssue/PubDate/Year")
        if not year:
            medline_date = article.findtext(
                ".//JournalIssue/PubDate/MedlineDate"
            )
            year = medline_date[:4] if medline_date else "unknown"

        papers.append(
            Paper(
                paper_id=f"pubmed:{pmid}",
                title=title,
                abstract=abstract or "(no abstract available)",
                authors=authors,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                published=year,
                source="pubmed",
            )
        )

    return papers


def search_all(topic, max_results=10):
    """Search both sources and preserve results if one source fails."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results < 1:
        raise ValueError("max_results must be a positive integer.")

    papers = []

    for name, search_function in (
        ("ArXiv", search_arxiv),
        ("PubMed", search_pubmed),
    ):
        try:
            papers.extend(search_function(topic, max_results))
        except Exception as error:
            print(f"[warning] {name} search failed: {error}")

    return papers


if __name__ == "__main__":
    for paper in search_all("machine learning drug discovery", max_results=3):
        print(f"[{paper.source}] {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   Published: {paper.published}")
        print(f"   URL: {paper.url}")
        print(f"   Abstract: {paper.abstract[:150]}...\n")
