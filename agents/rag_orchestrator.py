
"""Connect retrieved research context to the existing LangChain workflow."""

from agents.orchestrator import run_research_workflow
from services.vector_store import search_papers as pinecone_search_papers


def run_rag_research(
    research_topic: str,
    search_papers,
    top_k: int = 3,
) -> dict:
    """Run research using relevant paper chunks from a vector database."""

    if not isinstance(research_topic, str) or not research_topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    if not callable(search_papers):
        raise ValueError("search_papers must be callable.")

    retrieved_papers = search_papers(research_topic, top_k=top_k)

    if not retrieved_papers:
        raise ValueError("No relevant research papers found.")

    context_parts = []
    citation_metadata = []

    for index, paper in enumerate(retrieved_papers, start=1):
        if not isinstance(paper, dict):
            raise ValueError("Each retrieved paper must be a dictionary.")

        title = paper.get("title")
        source = paper.get("source")
        url = paper.get("url")
        text = paper.get("text")

        if not isinstance(text, str) or not text.strip():
            continue

        title = title.strip() if isinstance(title, str) else "Title unavailable"
        source = source.strip() if isinstance(source, str) else "Source unavailable"
        url = url.strip() if isinstance(url, str) else "URL unavailable"

        context_parts.append(
            f"Evidence [{index}]\n"
            f"Title: {title}\n"
            f"Source: {source}\n"
            f"URL: {url}\n"
            f"Text: {text.strip()}"
        )

        citation_metadata.append({
            "evidence_id": index,
            "title": title,
            "source": source,
            "url": url,
        })

    if not context_parts:
        raise ValueError("Retrieved papers contain no usable text.")

    paper_text = "\n\n".join(context_parts)

    result = run_research_workflow(
        research_topic=research_topic,
        paper_text=paper_text,
    )

    if not isinstance(result, dict):
        raise ValueError("Research workflow must return a dictionary.")

    result["retrieved_papers"] = retrieved_papers
    result["retrieval_count"] = len(context_parts)
    result["citation_metadata"] = citation_metadata

    return result


def run_pinecone_rag_research(
    research_topic: str,
    top_k: int = 3,
) -> dict:
    """Run research using papers retrieved from Pinecone."""

    return run_rag_research(
        research_topic=research_topic,
        search_papers=pinecone_search_papers,
        top_k=top_k,
    )
