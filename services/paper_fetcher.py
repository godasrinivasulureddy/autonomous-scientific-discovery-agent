
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field

import arxiv
import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# These publication types are not sufficient evidence of peer review.
EXCLUDED_PUBLICATION_TYPES = {
    "preprint",
    "review",
    "systematic review",
    "meta-analysis",
    "editorial",
    "comment",
    "letter",
    "news",
    "published erratum",
    "expression of concern",
    "retracted publication",
    "retraction of publication",
}

NON_RESEARCH_PUBLICATION_TYPES = {
    "bibliography",
    "biography",
    "case reports",
    "clinical conference",
    "congresses",
    "consensus development conference",
    "directory",
    "guideline",
    "practice guideline",
    "technical report",
}


@dataclass
class Paper:
    paper_id: str
    title: str
    abstract: str
    authors: list
    url: str
    published: str
    source: str
    publication_types: list = field(default_factory=list)
    peer_review_status: str = "unverified"

    def to_dict(self):
        return asdict(self)


def build_arxiv_query(topic):
    """Convert a topic into an ArXiv all-fields query."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    words = topic.split()
    return " AND ".join(f"all:{word}" for word in words)


def search_arxiv(topic, max_results=10, peer_reviewed_only=False):
    """
    Search ArXiv and return structured metadata.

    An ArXiv record alone does not establish peer-review status.
    Therefore, ArXiv results are excluded when peer-reviewed-only
    filtering is requested.
    """
    if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results < 1:
        raise ValueError("max_results must be a positive integer.")

    if not isinstance(peer_reviewed_only, bool):
        raise ValueError("peer_reviewed_only must be a boolean.")

    query = build_arxiv_query(topic)

    if peer_reviewed_only:
        return []

    client = arxiv.Client(
        page_size=max_results,
        delay_seconds=3,
        num_retries=3,
    )

    search = arxiv.Search(
        query=query,
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
                publication_types=["Preprint"],
                peer_review_status="unverified",
            )
        )

    return papers


def _normalize_publication_type(value):
    """Normalize publication types for consistent comparisons."""
    if not isinstance(value, str):
        return ""

    return " ".join(value.casefold().split())


def _is_eligible_pubmed_article(publication_types):
    """
    Conservatively filter PubMed publication metadata.

    Eligibility means the available publication types do not identify
    the record as an excluded publication. It does NOT prove peer review.
    Journal-level verification is still required for confirmed status.
    """
    if not isinstance(publication_types, (list, tuple, set)):
        return False

    normalized_types = {
        _normalize_publication_type(value)
        for value in publication_types
        if isinstance(value, str) and value.strip()
    }

    if not normalized_types:
        return False

    # Reject the record if any listed type is explicitly excluded.
    if normalized_types.intersection(EXCLUDED_PUBLICATION_TYPES):
        return False

    # Reject records identified only by non-research categories.
    if normalized_types.issubset(NON_RESEARCH_PUBLICATION_TYPES):
        return False

    return True


def search_pubmed(topic, max_results=10, peer_reviewed_only=False):
    """
    Search PubMed and return structured paper metadata.

    peer_reviewed_only applies a conservative publication-type filter.
    Eligible records are marked eligible_for_verification, not verified.
    """
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results < 1:
        raise ValueError("max_results must be a positive integer.")

    if not isinstance(peer_reviewed_only, bool):
        raise ValueError("peer_reviewed_only must be a boolean.")

    # Over-fetch candidate IDs when filtering for peer-reviewed papers
    # because latest records frequently contain reviews, editorials, and non-research items.
    query_retmax = max(max_results * 5, 20) if peer_reviewed_only else max_results

    response = requests.get(
        f"{EUTILS}/esearch.fcgi",
        params={
            "db": "pubmed",
            "term": topic.strip(),
            "retmax": query_retmax,
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
        pmid = article.findtext(
            ".//MedlineCitation/PMID",
            default="",
        ).strip()

        if not pmid:
            continue

        publication_types = [
            "".join(element.itertext()).strip()
            for element in article.findall(
                ".//MedlineCitation/Article/"
                "PublicationTypeList/PublicationType"
            )
            if "".join(element.itertext()).strip()
        ]

        eligible = _is_eligible_pubmed_article(publication_types)

        if peer_reviewed_only and not eligible:
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
                authors.append(
                    f"{first_name or ''} {last_name}".strip()
                )

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
                publication_types=publication_types,
                peer_review_status=(
                    "eligible_for_verification"
                    if eligible
                    else "unverified"
                ),
            )
        )

        if len(papers) >= max_results:
            break

    return papers


def search_all(topic, max_results=10, peer_reviewed_only=False):
    """Search both sources and preserve results if one source fails."""
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if not isinstance(max_results, int) or isinstance(max_results, bool) or max_results < 1:
        raise ValueError("max_results must be a positive integer.")

    if not isinstance(peer_reviewed_only, bool):
        raise ValueError("peer_reviewed_only must be a boolean.")

    papers = []

    search_functions = (
        ("ArXiv", search_arxiv),
        ("PubMed", search_pubmed),
    )

    for name, search_function in search_functions:
        try:
            results = search_function(
                topic.strip(),
                max_results,
                peer_reviewed_only=peer_reviewed_only,
            )
            papers.extend(results)
        except Exception as error:
            print(f"[warning] {name} search failed: {error}")

    return papers


if __name__ == "__main__":
    for paper in search_all(
        "machine learning drug discovery",
        max_results=3,
        peer_reviewed_only=True,
    ):
        print(f"[{paper.source}] {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   Published: {paper.published}")
        print(f"   Publication types: {', '.join(paper.publication_types)}")
        print(f"   Review status: {paper.peer_review_status}")
        print(f"   URL: {paper.url}")
        print(f"   Abstract: {paper.abstract[:150]}...\n")
