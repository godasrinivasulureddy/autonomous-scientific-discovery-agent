
"""Select approved experiment configurations using past rewards."""

import random


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
