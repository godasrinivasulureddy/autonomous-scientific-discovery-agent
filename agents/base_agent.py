
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Common interface for scientific discovery agents."""

    @abstractmethod
    def run(self, input_data: dict) -> dict:
        """Process input data and return structured results."""
        pass


AGENT_ROLES = {
    "literature_reviewer": (
        "Summarize research papers and identify research gaps."
    ),
    "hypothesis_generator": (
        "Generate testable scientific hypotheses."
    ),
    "code_executor": (
        "Execute approved, controlled experiments."
    ),
    "statistical_critic": (
        "Evaluate experimental results and limitations."
    ),
}
