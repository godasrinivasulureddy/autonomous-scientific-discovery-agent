
import json

from agents import repair_learning


def test_successful_repair_records_and_persists_reward(
    tmp_path, monkeypatch
):
    history_file = tmp_path / "repair_rewards.json"

    monkeypatch.setattr(
        repair_learning,
        "run_with_auto_repair",
        lambda code, max_corrections=2: {
            "status": "success",
            "attempts": 1,
            "result": {"status": "success"},
            "history": [{"attempt": 1, "status": "success"}],
        },
    )

    outcome = repair_learning.run_and_learn(
        "print(sum([1, 2, 3]))",
        history_file,
    )

    assert outcome["feedback"]["reward"] == 1.0
    assert outcome["feedback"]["accepted"] is True
    assert outcome["average_repair_reward"] == 1.0

    saved = json.loads(history_file.read_text(encoding="utf-8"))
    assert saved["code_repair"] == [1.0]


def test_failed_repair_records_zero_reward(tmp_path, monkeypatch):
    history_file = tmp_path / "repair_rewards.json"

    monkeypatch.setattr(
        repair_learning,
        "run_with_auto_repair",
        lambda code, max_corrections=2: {
            "status": "failed",
            "attempts": 2,
            "result": {"status": "error"},
            "history": [],
        },
    )

    outcome = repair_learning.run_and_learn(
        "print(sum([1, 2, 3]))",
        history_file,
    )

    assert outcome["feedback"]["reward"] == 0.0
    assert outcome["feedback"]["accepted"] is False

    saved = json.loads(history_file.read_text(encoding="utf-8"))
    assert saved["code_repair"] == [0.0]


def test_repair_rewards_accumulate_across_runs(tmp_path, monkeypatch):
    history_file = tmp_path / "repair_rewards.json"

    monkeypatch.setattr(
        repair_learning,
        "run_with_auto_repair",
        lambda code, max_corrections=2: {
            "status": "success",
            "attempts": 2,
            "result": {"status": "success"},
            "history": [],
        },
    )

    first = repair_learning.run_and_learn(
        "print(sum([1, 2, 3]))",
        history_file,
    )
    second = repair_learning.run_and_learn(
        "print(sum([1, 2, 3]))",
        history_file,
    )

    assert first["average_repair_reward"] == 0.5
    assert second["average_repair_reward"] == 0.5

    saved = json.loads(history_file.read_text(encoding="utf-8"))
    assert saved["code_repair"] == [0.5, 0.5]
