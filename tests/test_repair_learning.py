
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

    run_history_file = tmp_path / "repair_rewards_runs.json"
    records = json.loads(run_history_file.read_text(encoding="utf-8"))

    assert len(records) == 1
    assert records[0]["strategy"] == "code_repair"
    assert records[0]["status"] == "success"
    assert records[0]["attempts"] == 1
    assert records[0]["reward"] == 1.0
    assert records[0]["accepted"] is True
    assert records[0]["history"] == [
        {"attempt": 1, "status": "success"}
    ]


def test_failed_repair_records_zero_reward(tmp_path, monkeypatch):
    history_file = tmp_path / "repair_rewards.json"

    monkeypatch.setattr(
        repair_learning,
        "run_with_auto_repair",
        lambda code, max_corrections=2: {
            "status": "failed",
            "attempts": 2,
            "result": {"status": "error"},
            "history": [
                {"attempt": 1, "status": "error"},
                {"attempt": 2, "status": "error"},
            ],
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

    run_history_file = tmp_path / "repair_rewards_runs.json"
    records = json.loads(run_history_file.read_text(encoding="utf-8"))

    assert len(records) == 1
    assert records[0]["strategy"] == "code_repair"
    assert records[0]["status"] == "failed"
    assert records[0]["attempts"] == 2
    assert records[0]["reward"] == 0.0
    assert records[0]["accepted"] is False


def test_repair_rewards_accumulate_across_runs(tmp_path, monkeypatch):
    history_file = tmp_path / "repair_rewards.json"

    monkeypatch.setattr(
        repair_learning,
        "run_with_auto_repair",
        lambda code, max_corrections=2: {
            "status": "success",
            "attempts": 2,
            "result": {"status": "success"},
            "history": [
                {"attempt": 1, "status": "error"},
                {"attempt": 2, "status": "success"},
            ],
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

    run_history_file = tmp_path / "repair_rewards_runs.json"
    records = json.loads(run_history_file.read_text(encoding="utf-8"))

    assert len(records) == 2
    assert all(record["strategy"] == "code_repair" for record in records)
    assert all(record["status"] == "success" for record in records)
    assert all(record["attempts"] == 2 for record in records)
    assert all(record["reward"] == 0.5 for record in records)


def test_repair_run_history_persists_across_calls(tmp_path, monkeypatch):
    """Ensure separate calls append records instead of overwriting them."""
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

    repair_learning.run_and_learn("print(1)", history_file)
    repair_learning.run_and_learn("print(2)", history_file)

    records = json.loads(
        (tmp_path / "repair_rewards_runs.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(records) == 2
    assert records[0]["attempts"] == 1
    assert records[1]["attempts"] == 1
