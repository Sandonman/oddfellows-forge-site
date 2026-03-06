from __future__ import annotations

import re
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SMOKE_MATRIX_PATH = ROOT / "tests" / "SMOKE_MATRIX.md"


EXPECTED_VALIDATION_COMMANDS = [
    "PYTHONPATH=src pytest -q",
    "PYTHONPATH=src pytest -q tests/test_data_schema_basics.py",
    "PYTHONPATH=src pytest -q tests/test_concise_rendering_contracts.py",
    "PYTHONPATH=src pytest -q tests/test_export_summary.py",
    "PYTHONPATH=src pytest -q tests/test_persistence.py tests/test_undo_checkpoints.py tests/test_status_transitions.py",
]


def _extract_validation_commands(markdown: str) -> list[str]:
    block_match = re.search(r"## Validation commands\n\n```bash\n(.*?)\n```", markdown, flags=re.S)
    assert block_match is not None, "tests/SMOKE_MATRIX.md must contain a bash validation commands block"
    return [line.strip() for line in block_match.group(1).splitlines() if line.strip().startswith("PYTHONPATH=")]


def test_python_module_entrypoint_invokes_run_app(monkeypatch):
    calls: list[str] = []

    def _fake_run_app() -> None:
        calls.append("run")

    monkeypatch.setattr("cc_v3.app.run_app", _fake_run_app)
    runpy.run_module("cc_v3.__main__", run_name="__main__")

    assert calls == ["run"]


def test_smoke_matrix_validation_commands_match_release_assumptions():
    markdown = SMOKE_MATRIX_PATH.read_text(encoding="utf-8")
    commands = _extract_validation_commands(markdown)

    assert commands == EXPECTED_VALIDATION_COMMANDS

    for command in commands[1:]:
        for token in command.split()[3:]:
            assert (ROOT / token).is_file(), f"Referenced smoke test path does not exist: {token}"
