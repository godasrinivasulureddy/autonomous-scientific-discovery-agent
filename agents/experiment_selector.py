
"""Select approved experiment configurations using past rewards."""

import random
import json
from pathlib import Path


class ExperimentSelector:
    """Learn which approved experiment configuration earns better rewards."""

    def __init__(self, exploration_rate: float = 0.2):
        if not 0 <= exploration_rate <= 1:
            raise ValueError("Exploration rate must be between 0 and 1.")

        self.exploration_rate = exploration_rate
        self.rewards = {}

    def select(self, experiment_options: list[str]) -> str:
        """Choose an experiment using epsilon-greedy selection."""

        if not experiment_options:
            raise ValueError("Experiment options cannot be empty.")

        if random.random() < self.exploration_rate:
            return random.choice(experiment_options)

        return max(
            experiment_options,
            key=lambda option: (
                sum(self.rewards.get(option, []))
                / len(self.rewards.get(option, []))
                if self.rewards.get(option)
                else 0.0
            ),
        )

    def update(self, experiment_name: str, reward: float):
        """Store a reward for future experiment selection."""

        if not 0 <= reward <= 1:
            raise ValueError("Reward must be between 0 and 1.")

        self.rewards.setdefault(experiment_name, []).append(reward)

    def average_reward(self, experiment_name: str) -> float:
        """Return the historical average reward."""

        rewards = self.rewards.get(experiment_name, [])

        return sum(rewards) / len(rewards) if rewards else 0.0



    def save(self, file_path: str) -> None:
        """Save reward history to a JSON file."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as file:
            json.dump(self.rewards, file, indent=2)

    def load(self, file_path: str) -> None:
        """Load previously saved reward history."""
        path = Path(file_path)

        if not path.exists():
            return

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Invalid learning history format.")

        for name, rewards in data.items():
            if (
                not isinstance(name, str)
                or not isinstance(rewards, list)
                or any(
                    isinstance(reward, bool)
                    or not isinstance(reward, (int, float))
                    or not 0 <= reward <= 1
                    for reward in rewards
                )
            ):
                raise ValueError("Invalid reward history.")

        self.rewards = data

