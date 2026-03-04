# task-timer

Simple CLI task time tracker.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python -m task_timer.cli add-task "Write docs"
python -m task_timer.cli start 1
python -m task_timer.cli stop 1
python -m task_timer.cli status
python -m task_timer.cli report
```

Data is stored in `data/tasks.json`.
