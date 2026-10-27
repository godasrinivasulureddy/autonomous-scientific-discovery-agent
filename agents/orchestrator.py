
from typing import Any
from agents.code_executor import execute_experiment
from agents.langchain_workflow import run_langchain_research
from agents.memory_manager import AgentMemoryManager
from agents.statistical_critic import evaluate_experiment_results


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


def _validate_top_k(top_k: int) -> None:
    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k < 1
    ):
        raise ValueError("top_k must be a positive integer.")


def run_research_workflow(
    research_topic: str,
    paper_text: str,
    experiment_values: list[float] | None = None,
    memory_manager: AgentMemoryManager | None = None,
    enable_statistical_critic: bool = True,
) -> dict:
    """Coordinate scientific research agents using LangChain with memory and critic."""
    _validate_research_topic(research_topic)

    if not isinstance(paper_text, str) or not paper_text.strip():
        raise ValueError("Paper text cannot be empty.")

    research_result = run_langchain_research(
        topic=research_topic.strip(),
        paper_text=paper_text,
        experiment_values=experiment_values,
        memory_manager=memory_manager,
        enable_statistical_critic=enable_statistical_critic,
    )

    result: dict[str, Any] = {
        "research_topic": research_topic.strip(),
        "literature_review": research_result["literature_review"],
        "hypothesis": research_result["hypothesis"],
    }

    if experiment_values is not None:
        result["experiment"] = research_result.get("experiment_result", {})
    else:
        result["experiment"] = {
            "status": "not_executed",
            "reason": "An approved experiment and dataset are required.",
        }

    if "statistical_critic_result" in research_result:
        result["statistical_critic_result"] = research_result["statistical_critic_result"]

    if "memory_context" in research_result:
        result["memory_context"] = research_result["memory_context"]

    return result


def run_approved_experiment(values: list[float]) -> dict:
    """Execute a predefined statistical experiment."""
    return execute_experiment(
        experiment_name="descriptive_statistics",
        values=values,
    )


def _fetch_unique_papers(research_topic: str, max_results: int) -> list:
    """Fetch eligible papers and remove duplicates by paper ID."""
    from services.paper_fetcher import search_all

    papers = search_all(
        research_topic,
        max_results=max_results,
        peer_reviewed_only=True,
    )

    unique_papers = {}
    for paper in papers:
        paper_id = getattr(paper, "paper_id", None)
        if isinstance(paper_id, str) and paper_id.strip():
            unique_papers.setdefault(paper_id, paper)

    return list(unique_papers.values())


def _process_papers(papers: list) -> list[dict]:
    """Process papers and retain records containing usable text."""
    from services.pdf_processor import process_paper

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

    return processed_papers


def run_research_from_papers(
    research_topic: str,
    max_results: int = 3,
) -> dict:
    """Fetch scientific papers and run the research agents."""
    _validate_research_topic(research_topic)
    _validate_max_results(max_results)

    papers = _fetch_unique_papers(research_topic.strip(), max_results)

    if not papers:
        raise ValueError("No research papers found for this topic.")

    processed_papers = _process_papers(papers)
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
        research_topic=research_topic.strip(),
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
    """Fetch, process, and store research papers in Pinecone."""
    from services.vector_store import paper_exists, store_paper
    from services.pdf_processor import process_paper

    _validate_research_topic(research_topic)
    _validate_max_results(max_results)

    papers = _fetch_unique_papers(research_topic.strip(), max_results)

    stored_papers = []
    skipped_papers = []
    failed_papers = []

    for paper in papers:
        paper_id = getattr(paper, "paper_id", None)

        if not isinstance(paper_id, str) or not paper_id.strip():
            continue

        try:
            already_exists = paper_exists(paper_id)
        except Exception as error:
            # Preserve fallback behavior: attempt ingestion if the
            # duplicate check fails. The storage layer handles upserts.
            print(
                f"[warning] Could not check existing paper "
                f"{paper_id}: {error}"
            )
            already_exists = False

        if already_exists:
            skipped_papers.append(paper_id)
            continue

        try:
            record = process_paper(paper)

            if not isinstance(record, dict):
                raise ValueError(
                    "Paper processor returned an invalid record."
                )

            full_text = record.get("full_text")
            if not isinstance(full_text, str) or not full_text.strip():
                raise ValueError("Paper has no usable text.")

            title = record.get("title") or getattr(
                paper, "title", "Title unavailable"
            )
            source = record.get("source") or getattr(
                paper, "source", "unknown"
            )
            url = record.get("url") or getattr(paper, "url", "")

            # Keep the original five arguments for objects that do not
            # provide valid publication metadata. This preserves
            # compatibility with existing callers and tests.
            store_kwargs = {
                "paper_id": paper_id,
                "title": title,
                "text": full_text.strip(),
                "source": source,
                "url": url,
            }

            publication_types = getattr(
                paper, "publication_types", None
            )
            peer_review_status = getattr(
                paper, "peer_review_status", None
            )

            # Real Paper records provide a list and a string. Mock or
            # legacy records without valid metadata use the defaults
            # already supported by store_paper().
            if (
                isinstance(publication_types, list)
                and isinstance(peer_review_status, str)
            ):
                store_kwargs["publication_types"] = publication_types
                store_kwargs["peer_review_status"] = peer_review_status

            storage_result = store_paper(**store_kwargs)
            stored_papers.append(storage_result)

        except Exception as error:
            failed_papers.append({
                "paper_id": paper_id,
                "reason": str(error),
            })

    if failed_papers:
        status = (
            "partial"
            if stored_papers or skipped_papers
            else "failed"
        )
    elif stored_papers or skipped_papers:
        status = "completed"
    else:
        status = "failed"

    return {
        "research_topic": research_topic.strip(),
        "status": status,
        "paper_count": len(stored_papers),
        "stored_papers": stored_papers,
        "skipped_papers": skipped_papers,
        "failed_papers": failed_papers,
    }


def run_experiment_with_feedback(
    values: list[float],
    use_docker: bool = True,
    memory_manager: AgentMemoryManager | None = None,
) -> dict:
    """Run approved statistics and evaluate with both feedback agent and statistical critic."""
    from agents.code_executor import execute_experiment, execute_experiment_in_docker
    from agents.feedback_agent import evaluate_experiment

    if use_docker:
        experiment_result = execute_experiment_in_docker(
            experiment_name="descriptive_statistics",
            values=values,
            include_metadata=True,
        )
    else:
        experiment_result = execute_experiment(
            experiment_name="descriptive_statistics",
            values=values,
            include_metadata=True,
        )

    feedback = evaluate_experiment(experiment_result)

    # Day 5 integration: Statistical Critic evaluation
    try:
        statistical_critic_result = evaluate_experiment_results(
            hypothesis="Empirical measurement of distribution parameters",
            experiment_result=experiment_result,
        )
    except Exception as exc:
        statistical_critic_result = {
            "status": "error",
            "error": str(exc),
        }

    # Record into memory if provided
    if memory_manager:
        memory_manager.add_interaction(
            role="code_executor",
            content=f"Executed experiment with {len(values)} values. Result status: {experiment_result.get('status')}",
            metadata={"experiment": "descriptive_statistics", "use_docker": use_docker},
        )
        memory_manager.add_interaction(
            role="statistical_critic",
            content=statistical_critic_result.get("criticism", str(statistical_critic_result)),
            metadata={"status": statistical_critic_result.get("status")},
        )

    return {
        "experiment": experiment_result,
        "feedback": feedback,
        "statistical_critic": statistical_critic_result,
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

    if (
        not isinstance(rounds, int)
        or isinstance(rounds, bool)
        or rounds < 1
    ):
        raise ValueError("Rounds must be a positive integer.")

    if any(
        not isinstance(name, str) or not name.strip()
        for name in experiment_options
    ):
        raise ValueError("Experiment names must be non-empty strings.")

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
    """Ingest eligible papers, retrieve evidence, and run RAG."""
    from agents.rag_orchestrator import run_pinecone_rag_research

    _validate_research_topic(research_topic)
    _validate_max_results(max_results)
    _validate_top_k(top_k)

    ingestion = ingest_research_papers(
        research_topic=research_topic.strip(),
        max_results=max_results,
    )

    if ingestion["status"] == "failed":
        return {
            "research_topic": research_topic.strip(),
            "pipeline_status": "failed",
            "ingestion": ingestion,
            "error": (
                "No papers were successfully stored; "
                "check ingestion errors."
            ),
        }

    research = run_pinecone_rag_research(
        research_topic=research_topic.strip(),
        top_k=top_k,
    )

    research["ingestion"] = ingestion
    research["pipeline_status"] = (
        "completed"
        if ingestion["status"] == "completed"
        else "partial"
    )

    return research
