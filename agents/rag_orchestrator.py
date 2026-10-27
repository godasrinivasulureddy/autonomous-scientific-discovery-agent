
"""Connect retrieved research context to the existing LangChain workflow."""

from agents.orchestrator import run_research_workflow
from agents.memory_manager import AgentMemoryManager
from services.vector_store import search_papers as pinecone_search_papers


def run_rag_research(
    research_topic: str,
    search_papers,
    top_k: int = 3,
    peer_reviewed_only: bool = False,
    experiment_values: list[float] | None = None,
    memory_manager: AgentMemoryManager | None = None,
    enable_statistical_critic: bool = True,
) -> dict:
    """Run research using relevant paper chunks from a vector database."""

    if not isinstance(research_topic, str) or not research_topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    if not isinstance(peer_reviewed_only, bool):
        raise ValueError("peer_reviewed_only must be a boolean.")

    if not callable(search_papers):
        raise ValueError("search_papers must be callable.")

    search_args = {"top_k": top_k}

    if peer_reviewed_only:
        search_args["peer_reviewed_only"] = True

    retrieved_papers = search_papers(
        research_topic.strip(),
        **search_args,
    )

    if not retrieved_papers:
        raise ValueError("No relevant research papers found.")

    context_parts = []
    citation_metadata = []

    for paper in retrieved_papers:
        if not isinstance(paper, dict):
            raise ValueError("Each retrieved paper must be a dictionary.")

        text = paper.get("text")

        if not isinstance(text, str) or not text.strip():
            continue

        title = paper.get("title")
        source = paper.get("source")
        url = paper.get("url")

        title = (
            title.strip()
            if isinstance(title, str) and title.strip()
            else "Title unavailable"
        )
        source = (
            source.strip()
            if isinstance(source, str) and source.strip()
            else "Source unavailable"
        )
        url = (
            url.strip()
            if isinstance(url, str) and url.strip()
            else "URL unavailable"
        )

        evidence_id = len(citation_metadata) + 1

        context_parts.append(
            f"Evidence [{evidence_id}]\n"
            f"Title: {title}\n"
            f"Source: {source}\n"
            f"URL: {url}\n"
            f"Text: {text.strip()}"
        )

        citation_metadata.append(
            {
                "evidence_id": evidence_id,
                "title": title,
                "source": source,
                "url": url,
            }
        )

    if not context_parts:
        raise ValueError("Retrieved papers contain no usable text.")

    result = run_research_workflow(
        research_topic=research_topic.strip(),
        paper_text="\n\n".join(context_parts),
        experiment_values=experiment_values,
        memory_manager=memory_manager,
        enable_statistical_critic=enable_statistical_critic,
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
    peer_reviewed_only: bool = False,
    experiment_values: list[float] | None = None,
    memory_manager: AgentMemoryManager | None = None,
    enable_statistical_critic: bool = True,
) -> dict:
    """Run research using papers retrieved from Pinecone."""

    return run_rag_research(
        research_topic=research_topic,
        search_papers=pinecone_search_papers,
        top_k=top_k,
        peer_reviewed_only=peer_reviewed_only,
        experiment_values=experiment_values,
        memory_manager=memory_manager,
        enable_statistical_critic=enable_statistical_critic,
    )
