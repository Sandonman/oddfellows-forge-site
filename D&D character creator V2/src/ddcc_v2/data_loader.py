"""Load local SRD JSON datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DATA_FILES = {
    "classes": "classes.json",
    "species": "species.json",
    "backgrounds": "backgrounds.json",
    "skills": "skills.json",
    "equipment": "equipment.json",
    "spells": "spells.json",
    "alignments": "alignments.json",
}


def data_dir() -> Path:
    return Path(__file__).resolve().parent / "data"


def load_json(filename: str) -> Any:
    path = data_dir() / filename
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_dataset() -> dict[str, Any]:
    return {name: load_json(filename) for name, filename in DATA_FILES.items()}


def index_by_name(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {r["name"]: r for r in records}
