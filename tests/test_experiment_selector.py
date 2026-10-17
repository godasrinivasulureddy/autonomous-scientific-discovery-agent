
import pytest

from agents.experiment_selector import ExperimentSelector


def test_selector_learns_from_rewards():
    selector = ExperimentSelector(exploration_rate=0.0)

    selector.update("configuration_A", 0.2)
    selector.update("configuration_B", 0.9)

    assert selector.select(
        ["configuration_A", "configuration_B"]
    ) == "configuration_B"


def test_average_reward():
    selector = ExperimentSelector()

    selector.update("configuration_A", 0.4)
    selector.update("configuration_A", 0.8)

    assert selector.average_reward("configuration_A") == pytest.approx(0.6)


def test_empty_options_rejected():
    selector = ExperimentSelector()

    with pytest.raises(ValueError):
        selector.select([])


def test_invalid_reward_rejected():
    selector = ExperimentSelector()

    with pytest.raises(ValueError):
        selector.update("configuration_A", 1.5)


def test_exploration_selects_valid_option():
    selector = ExperimentSelector(exploration_rate=1.0)

    options = ["configuration_A", "configuration_B"]

    for _ in range(10):
        assert selector.select(options) in options
