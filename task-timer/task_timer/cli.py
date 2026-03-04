import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TASKS_FILE = DATA_DIR / "tasks.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_store() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]", encoding="utf-8")


def load_tasks() -> List[Dict[str, Any]]:
    ensure_store()
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))


def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    ensure_store()
    TASKS_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def next_id(tasks: List[Dict[str, Any]]) -> int:
    if not tasks:
        return 1
    return max(t["id"] for t in tasks) + 1


def get_task(tasks: List[Dict[str, Any]], task_id: int) -> Dict[str, Any]:
    for t in tasks:
        if t["id"] == task_id:
            return t
    raise ValueError(f"Task {task_id} not found")


def cmd_add_task(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    task = {
        "id": next_id(tasks),
        "name": args.name,
        "created_at": now_iso(),
        "started_at": None,
        "is_running": False,
        "accumulated_seconds": 0.0,
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added task {task['id']}: {task['name']}")
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    task = get_task(tasks, args.id)
    if task["is_running"]:
        print(f"Task {task['id']} already running")
        return 1
    task["is_running"] = True
    task["started_at"] = now_iso()
    save_tasks(tasks)
    print(f"Started task {task['id']}: {task['name']}")
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    task = get_task(tasks, args.id)
    if not task["is_running"]:
        print(f"Task {task['id']} is not running")
        return 1

    started = datetime.fromisoformat(task["started_at"])
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    task["accumulated_seconds"] += max(0.0, elapsed)
    task["is_running"] = False
    task["started_at"] = None
    save_tasks(tasks)
    print(f"Stopped task {task['id']}: +{elapsed:.2f}s")
    return 0


def live_elapsed(task: Dict[str, Any]) -> float:
    total = float(task["accumulated_seconds"])
    if task["is_running"] and task["started_at"]:
        started = datetime.fromisoformat(task["started_at"])
        total += max(0.0, (datetime.now(timezone.utc) - started).total_seconds())
    return total


def cmd_status(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    if args.id is not None:
        task = get_task(tasks, args.id)
        print(
            f"[{task['id']}] {task['name']} | running={task['is_running']} | total={live_elapsed(task):.2f}s"
        )
        return 0

    for task in tasks:
        print(
            f"[{task['id']}] {task['name']} | running={task['is_running']} | total={live_elapsed(task):.2f}s"
        )
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    tasks = load_tasks()
    if not tasks:
        print("No tasks available")
        return 0

    ranked = sorted(tasks, key=live_elapsed, reverse=True)
    for task in ranked:
        print(f"{task['id']},{task['name']},{live_elapsed(task):.2f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task-timer")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add-task", help="Add a new task")
    add.add_argument("name")
    add.set_defaults(func=cmd_add_task)

    start = sub.add_parser("start", help="Start a task timer")
    start.add_argument("id", type=int)
    start.set_defaults(func=cmd_start)

    stop = sub.add_parser("stop", help="Stop a task timer")
    stop.add_argument("id", type=int)
    stop.set_defaults(func=cmd_stop)

    status = sub.add_parser("status", help="Show task status")
    status.add_argument("id", nargs="?", type=int)
    status.set_defaults(func=cmd_status)

    report = sub.add_parser("report", help="Show time report")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
