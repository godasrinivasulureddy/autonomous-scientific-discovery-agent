
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





def test_save_and_load_learning_history(tmp_path):
    """Verify that learned rewards survive a new selector instance."""

    from agents.experiment_selector import ExperimentSelector

    history_file = tmp_path / "learning_history.json"

    # First instance learns from rewards.
    original = ExperimentSelector(exploration_rate=0.0)
    original.update("configuration_A", 0.2)
    original.update("configuration_B", 0.9)
    original.save(str(history_file))

    assert history_file.exists()

    # A new instance restores previous learning.
    restored = ExperimentSelector(exploration_rate=0.0)
    restored.load(str(history_file))

    assert restored.average_reward("configuration_A") == 0.2
    assert restored.average_reward("configuration_B") == 0.9

    assert restored.select([
        "configuration_A",
        "configuration_B",
    ]) == "configuration_B"


def test_load_missing_history_file(tmp_path):
    """Missing history should not crash the selector."""

    from agents.experiment_selector import ExperimentSelector

    selector = ExperimentSelector()

    selector.load(str(tmp_path / "missing.json"))

    assert selector.rewards == {}




def test_save_and_load_learning_history(tmp_path):
    """Verify that learned rewards survive a new selector instance."""

    from agents.experiment_selector import ExperimentSelector

    history_file = tmp_path / "learning_history.json"

    # First instance learns from rewards.
    original = ExperimentSelector(exploration_rate=0.0)
    original.update("configuration_A", 0.2)
    original.update("configuration_B", 0.9)
    original.save(str(history_file))

    assert history_file.exists()

    # A new instance restores previous learning.
    restored = ExperimentSelector(exploration_rate=0.0)
    restored.load(str(history_file))

    assert restored.average_reward("configuration_A") == 0.2
    assert restored.average_reward("configuration_B") == 0.9

    assert restored.select([
        "configuration_A",
        "configuration_B",
    ]) == "configuration_B"


def test_load_missing_history_file(tmp_path):
    """Missing history should not crash the selector."""

    from agents.experiment_selector import ExperimentSelector

    selector = ExperimentSelector()

    selector.load(str(tmp_path / "missing.json"))

    assert selector.rewards == {}


def test_load_invalid_history_file(tmp_path):
    """Invalid reward history should be rejected."""

    import json
    import pytest

    from agents.experiment_selector import ExperimentSelector

    history_file = tmp_path / "invalid_history.json"

    history_file.write_text(
        json.dumps({"configuration_A": [1.5]}),
        encoding="utf-8",
    )

    selector = ExperimentSelector()

    with pytest.raises(ValueError):
        selector.load(str(history_file))




def test_learning_orchestrator_persists_history(tmp_path, monkeypatch):
    """Verify rewards are saved and restored across separate runs."""

    from agents import orchestrator
    from agents.experiment_selector import ExperimentSelector

    history_file = tmp_path / "learning_history.json"

    def fake_experiment(values):
        return {
            "experiment": {
                "status": "success",
                "sample_size": len(values),
            },
            "feedback": {
                "accepted": True,
                "reward": len(values) / 100,
                "feedback": "Test feedback",
            },
        }

    monkeypatch.setattr(
        orchestrator,
        "run_experiment_with_feedback",
        fake_experiment,
    )

    options = {
        "small_sample": [10, 20, 30, 40],
    }

    # First run: create learning history.
    first = orchestrator.run_learning_experiments(
        experiment_options=options,
        rounds=2,
        history_path=str(history_file),
    )

    assert first["rounds"] == 2
    assert history_file.exists()

    selector = ExperimentSelector()
    selector.load(str(history_file))

    assert len(selector.rewards["small_sample"]) == 2

    # Second run: restore history and add another reward.
    second = orchestrator.run_learning_experiments(
        experiment_options=options,
        rounds=1,
        history_path=str(history_file),
    )

    assert second["rounds"] == 1

    selector = ExperimentSelector()
    selector.load(str(history_file))

    assert len(selector.rewards["small_sample"]) == 3
    assert selector.average_reward("small_sample") == 0.04

