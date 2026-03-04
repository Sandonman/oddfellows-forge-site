import json
import time
from pathlib import Path

import pytest

import task_timer.cli as cli


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    tasks_file = data_dir / "tasks.json"
    monkeypatch.setattr(cli, "DATA_DIR", data_dir)
    monkeypatch.setattr(cli, "TASKS_FILE", tasks_file)
    return tasks_file


def run_cmd(*args):
    return cli.main(list(args))


def read_tasks(tasks_file: Path):
    return json.loads(tasks_file.read_text(encoding="utf-8"))


def test_add_task_creates_json_and_entry(isolated_store):
    code = run_cmd("add-task", "Deep Work")
    assert code == 0
    tasks = read_tasks(isolated_store)
    assert len(tasks) == 1
    assert tasks[0]["name"] == "Deep Work"
    assert tasks[0]["id"] == 1


def test_start_sets_running_state(isolated_store):
    run_cmd("add-task", "Task A")
    code = run_cmd("start", "1")
    assert code == 0
    task = read_tasks(isolated_store)[0]
    assert task["is_running"] is True
    assert task["started_at"] is not None


def test_stop_accumulates_time_and_unsets_running(isolated_store):
    run_cmd("add-task", "Task B")
    run_cmd("start", "1")
    time.sleep(0.01)
    code = run_cmd("stop", "1")
    assert code == 0
    task = read_tasks(isolated_store)[0]
    assert task["is_running"] is False
    assert task["started_at"] is None
    assert task["accumulated_seconds"] > 0


def test_status_single_task_output(isolated_store, capsys):
    run_cmd("add-task", "Task C")
    code = run_cmd("status", "1")
    out = capsys.readouterr().out
    assert code == 0
    assert "[1] Task C" in out


def test_report_orders_by_total_time_desc(isolated_store, capsys):
    run_cmd("add-task", "Slow")
    run_cmd("add-task", "Fast")

    run_cmd("start", "1")
    time.sleep(0.02)
    run_cmd("stop", "1")

    run_cmd("start", "2")
    time.sleep(0.005)
    run_cmd("stop", "2")

    _ = capsys.readouterr()
    code = run_cmd("report")
    out = capsys.readouterr().out.strip().splitlines()
    assert code == 0
    assert out[0].startswith("1,Slow,")
    assert out[1].startswith("2,Fast,")
