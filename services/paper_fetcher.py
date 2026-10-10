import arxiv
import requests

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch_arxiv_basic(query, max_results=3):
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    return [
        {
            "id": r.get_short_id(),
            "title": r.title.strip(),
            "authors": [a.name for a in r.authors],
            "published": str(r.published.date()),
            "url": r.pdf_url,
        }
        for r in client.results(search)
    ]


def fetch_pubmed_basic(query, max_results=3):
    r = requests.get(
        f"{EUTILS}/esearch.fcgi",
        params={"db": "pubmed", "term": query, "retmax": max_results,
                "retmode": "json", "sort": "date"},
        timeout=30,
    )
    r.raise_for_status()
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        return []

    r = requests.get(
        f"{EUTILS}/esummary.fcgi",
        params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
        timeout=30,
    )
    r.raise_for_status()
    result = r.json()["result"]

    papers = []
    for pid in ids:
        item = result[pid]
        papers.append({
            "id": pid,
            "title": item.get("title", "").strip(),
            "authors": [a["name"] for a in item.get("authors", [])],
            "published": item.get("pubdate", "unknown"),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
        })
    return papers


if __name__ == "__main__":
    topic = "machine learning drug discovery"

    print("=== ArXiv ===")
    for p in fetch_arxiv_basic(topic):
        print(f"- {p['title']} ({p['published']})\n  {p['url']}")

    print("\n=== PubMed ===")
    for p in fetch_pubmed_basic(topic):
        print(f"- {p['title']} ({p['published']})\n  {p['url']}")