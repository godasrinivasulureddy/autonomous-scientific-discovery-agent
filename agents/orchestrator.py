
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
