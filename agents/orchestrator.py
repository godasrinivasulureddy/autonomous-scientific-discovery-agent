from agents.code_executor import execute_experiment
from agents.langchain_workflow import run_langchain_research


def _validate_research_topic(research_topic: str) -> None:
    if not isinstance(research_topic, str) or not research_topic.strip():
        raise ValueError("Research topic cannot be empty.")


def _validate_max_results(max_results: int) -> None:
    if (
        not isinstance(max_results, int)
        or isinstance(max_results, bool)
        or max_results < 1
    ):
        raise ValueError("max_results must be a positive integer.")


def run_research_workflow(
    research_topic: str,
    paper_text: str,
) -> dict:
    """Coordinate scientific research agents using LangChain."""

    _validate_research_topic(research_topic)

    if not isinstance(paper_text, str) or not paper_text.strip():
        raise ValueError("Paper text cannot be empty.")

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
    from services.pdf_processor import process_paper

    _validate_research_topic(research_topic)
    _validate_max_results(max_results)

    papers = search_all(research_topic, max_results=max_results)

    unique_papers = {}
    for paper in papers:
        paper_id = getattr(paper, "paper_id", None)
        if paper_id:
            unique_papers.setdefault(paper_id, paper)

    papers = list(unique_papers.values())

    if not papers:
        raise ValueError("No research papers found for this topic.")

    processed_papers = []
    for paper in papers:
        try:
            record = process_paper(paper)
        except Exception as error:
            print(
                f"[warning] Failed to process paper "
                f"{getattr(paper, 'paper_id', 'unknown')}: {error}"
            )
            continue

        if not isinstance(record, dict):
            continue

        full_text = record.get("full_text")
        if not isinstance(full_text, str) or not full_text.strip():
            continue

        processed_papers.append({
            "paper": paper,
            "record": record,
        })

    if not processed_papers:
        raise ValueError("No papers could be processed into usable text.")

    paper_text = "\n\n".join(
        f"Evidence [{index}]\n"
        f"Title: {item['record'].get('title', 'Title unavailable')}\n"
        f"Source: {item['record'].get('source', 'Source unavailable')}\n"
        f"URL: {item['record'].get('url', 'URL unavailable')}\n"
        f"Text: {item['record']['full_text'].strip()}"
        for index, item in enumerate(processed_papers, start=1)
    )

    result = run_research_workflow(
        research_topic=research_topic,
        paper_text=paper_text,
    )

    result["papers"] = [
        item["paper"].to_dict()
        for item in processed_papers
    ]
    result["paper_count"] = len(processed_papers)

    return result


def ingest_research_papers(
    research_topic: str,
    max_results: int = 3,
) -> dict:
    """Fetch scientific papers, process them, and store them in Pinecone."""

    from services.paper_fetcher import search_all
    from services.pdf_processor import process_paper
    from services.vector_store import store_paper

    _validate_research_topic(research_topic)
    _validate_max_results(max_results)

    papers = search_all(research_topic, max_results=max_results)

    unique_papers = {}
    for paper in papers:
        paper_id = getattr(paper, "paper_id", None)
        if paper_id:
            unique_papers.setdefault(paper_id, paper)

    stored_papers = []

    for paper in unique_papers.values():
        try:
            record = process_paper(paper)
        except Exception as error:
            print(
                f"[warning] Failed to process paper "
                f"{getattr(paper, 'paper_id', 'unknown')}: {error}"
            )
            continue

        if not isinstance(record, dict):
            continue

        full_text = record.get("full_text")
        if not isinstance(full_text, str) or not full_text.strip():
            continue

        result = store_paper(
            paper_id=paper.paper_id,
            title=record.get("title", getattr(paper, "title", "Title unavailable")),
            text=full_text.strip(),
            source=record.get("source", getattr(paper, "source", "unknown")),
            url=record.get("url", getattr(paper, "url", "")),
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


def run_learning_experiments(
    experiment_options: dict[str, list[float]],
    rounds: int = 3,
    history_path: str = "data/learning_history.json",
) -> dict:
    """Run approved experiments and persist reward-based learning."""

    from agents.experiment_selector import ExperimentSelector

    if not isinstance(experiment_options, dict) or not experiment_options:
        raise ValueError("Experiment options cannot be empty.")

    if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 1:
        raise ValueError("Rounds must be a positive integer.")

    selector = ExperimentSelector(exploration_rate=0.2)
    selector.load(history_path)

    history = []

    for _ in range(rounds):
        selected = selector.select(list(experiment_options))

        result = run_experiment_with_feedback(
            values=experiment_options[selected],
        )

        reward = result["feedback"]["reward"]
        selector.update(selected, reward)

        history.append({
            "configuration": selected,
            "reward": reward,
            "experiment": result["experiment"],
            "feedback": result["feedback"],
        })

    selector.save(history_path)

    return {
        "rounds": rounds,
        "history": history,
        "average_rewards": {
            name: selector.average_reward(name)
            for name in experiment_options
        },
    }



def run_full_research_pipeline(
    research_topic: str,
    max_results: int = 3,
    top_k: int = 3,
) -> dict:
    """Ingest papers into Pinecone, then run research using RAG."""

    from agents.rag_orchestrator import run_pinecone_rag_research

    _validate_research_topic(research_topic)
    _validate_max_results(max_results)

    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k < 1
    ):
        raise ValueError("top_k must be a positive integer.")

    ingestion = ingest_research_papers(
        research_topic=research_topic,
        max_results=max_results,
    )

    if ingestion["paper_count"] == 0:
        raise ValueError("No usable research papers were ingested.")

    research = run_pinecone_rag_research(
        research_topic=research_topic,
        top_k=top_k,
    )

    research["ingestion"] = ingestion
    research["pipeline_status"] = "completed"
    return research
