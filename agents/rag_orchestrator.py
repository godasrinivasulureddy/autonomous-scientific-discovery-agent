
"""Connect retrieved research context to the existing LangChain workflow."""

from agents.orchestrator import run_research_workflow
from services.vector_store import search_papers as pinecone_search_papers


def run_rag_research(
    research_topic: str,
    search_papers,
    top_k: int = 3,
) -> dict:
    """Run research using relevant paper chunks from a vector database."""

    if not research_topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # Member 3 will provide the actual Pinecone search function.
    retrieved_papers = search_papers(research_topic, top_k=top_k)

    if not retrieved_papers:
        raise ValueError("No relevant research papers found.")

    context_parts = []

    for paper in retrieved_papers:
        context_parts.append(
            f"Title: {paper['title']}\n"
            f"Source: {paper['source']}\n"
            f"URL: {paper['url']}\n"
            f"Text: {paper['text']}"
        )

    paper_text = "\n\n".join(context_parts)

    result = run_research_workflow(
        research_topic=research_topic,
        paper_text=paper_text,
    )

    result["retrieved_papers"] = retrieved_papers
    result["retrieval_count"] = len(retrieved_papers)

    return result




def run_pinecone_rag_research(
    research_topic: str,
    top_k: int = 3,
) -> dict:
    """Run the research agents using papers retrieved from Pinecone."""
    return run_rag_research(
        research_topic=research_topic,
        search_papers=pinecone_search_papers,
        top_k=top_k,
    )

