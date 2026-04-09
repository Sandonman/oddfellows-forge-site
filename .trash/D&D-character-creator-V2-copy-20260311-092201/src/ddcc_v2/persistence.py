"""Save/load character files."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Character


def save_character(character: Character, file_path: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(character.to_dict(), f, indent=2)


def load_character(file_path: str) -> Character:
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return Character.from_dict(data)
