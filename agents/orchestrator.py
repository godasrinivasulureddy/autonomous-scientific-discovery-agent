
from agents.code_executor import execute_experiment
from agents.langchain_workflow import run_langchain_research


def run_research_workflow(
    research_topic: str,
    paper_text: str,
) -> dict:
    """Coordinate scientific research agents using LangChain."""

    if not research_topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if not paper_text.strip():
        raise ValueError("Paper text cannot be empty.")

    # Run Literature Reviewer and Hypothesis Generator through LangChain
    research_result = run_langchain_research(
        topic=research_topic,
        paper_text=paper_text,
    )

    return {
        "research_topic": research_topic,
        "literature_review": research_result["literature_review"],
        "hypothesis": research_result["hypothesis"],
        "experiment": {
            "status": "not_executed",
            "reason": "An approved experiment and dataset are required.",
        },
    }


def run_approved_experiment(values: list[float]) -> dict:
    """Execute a predefined statistical experiment."""

    return execute_experiment(
        experiment_name="descriptive_statistics",
        values=values,
    )


def run_research_from_papers(
    research_topic: str,
    max_results: int = 3,
) -> dict:
    """Fetch scientific papers and run the research agents."""

    from services.paper_fetcher import search_all

    if not research_topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    # Step 1: Fetch papers from arXiv and PubMed
    papers = search_all(research_topic, max_results=max_results)

    # Remove duplicate papers using unique paper IDs
    unique_papers = {}

    for paper in papers:
        unique_papers.setdefault(paper.paper_id, paper)

    papers = list(unique_papers.values())

    if not papers:
        raise ValueError("No research papers found for this topic.")

    # Step 2: Extract PDF text when available
    from services.pdf_processor import process_paper

    processed_papers = [
        process_paper(paper)
        for paper in papers
    ]

    paper_text = "\n\n".join(
        f"Title: {record['title']}\n"
        f"Source: {record['source']}\n"
        f"URL: {record['url']}\n"
        f"Text: {record['full_text']}"
        for record in processed_papers
    )

    # Step 3: Run LangChain agent workflow
    result = run_research_workflow(
        research_topic=research_topic,
        paper_text=paper_text,
    )

    # Step 4: Include paper information
    result["papers"] = [
        paper.to_dict()
        for paper in papers
    ]
    result["paper_count"] = len(papers)

    return result




def ingest_research_papers(
    research_topic: str,
    max_results: int = 3,
) -> dict:
    """Fetch scientific papers, process them, and store them in Pinecone."""

    from services.paper_fetcher import search_all
    from services.pdf_processor import process_paper
    from services.vector_store import store_paper

    if not research_topic.strip():
        raise ValueError("Research topic cannot be empty.")

    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    papers = search_all(research_topic, max_results=max_results)

    unique_papers = {
        paper.paper_id: paper
        for paper in papers
    }

    stored_papers = []

    for paper in unique_papers.values():
        record = process_paper(paper)

        if not record["full_text"].strip():
            continue

        result = store_paper(
            paper_id=paper.paper_id,
            title=record["title"],
            text=record["full_text"],
            source=record["source"],
            url=record["url"],
        )

        stored_papers.append(result)

    return {
        "research_topic": research_topic,
        "paper_count": len(stored_papers),
        "stored_papers": stored_papers,
    }




def run_experiment_with_feedback(
    values: list[float],
) -> dict:
    """Run approved statistics in Docker and evaluate the result."""

    from agents.code_executor import execute_experiment_in_docker
    from agents.feedback_agent import evaluate_experiment

    experiment_result = execute_experiment_in_docker(
        experiment_name="descriptive_statistics",
        values=values,
    )

    feedback = evaluate_experiment(experiment_result)

    return {
        "experiment": experiment_result,
        "feedback": feedback,
    }
