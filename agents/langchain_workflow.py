
"""LangChain orchestration using the existing Gemini-powered agents."""

from langchain_core.runnables import RunnableLambda

from agents.literature_reviewer import review_literature
from agents.hypothesis_generator import generate_hypothesis


def run_langchain_research(topic: str, paper_text: str) -> dict:
    """Run literature review followed by hypothesis generation."""

    if not topic.strip() or not paper_text.strip():
        raise ValueError("Topic and paper text must not be empty.")

    def literature_step(data: dict) -> dict:
        review = review_literature(data["topic"], data["paper_text"])
        return {**data, "literature_review": review}

    def hypothesis_step(data: dict) -> dict:
        hypothesis = generate_hypothesis(
            data["topic"], data["literature_review"]
        )
        return {**data, "hypothesis": hypothesis}

    workflow = (
        RunnableLambda(literature_step)
        | RunnableLambda(hypothesis_step)
    )

    return workflow.invoke({
        "topic": topic,
        "paper_text": paper_text,
    })
