from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

MAX_LEVEL = 20


@dataclass(frozen=True)
class LevelSnapshot:
    class_name: str
    level: int
    proficiency_bonus: int
    gained_features: list[str]
    visible_features: list[str]
    spellcasting: dict[str, Any] | None


def _data_path(filename: str) -> Path:
    return Path(__file__).resolve().parent / "data" / filename


def load_classes(data_path: Path | None = None) -> dict[str, dict[str, Any]]:
    path = data_path or _data_path("classes.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["name"]: row for row in payload}


def _get_level_row(class_row: dict[str, Any], level: int) -> dict[str, Any]:
    if level < 1 or level > MAX_LEVEL:
        raise ValueError(f"level must be between 1 and {MAX_LEVEL}: {level}")

    progression = class_row.get("level_progression") or []
    for row in progression:
        if int(row.get("level", 0)) == level:
            return row
    raise ValueError(f"missing level progression row for level {level}")


def build_level_snapshot(
    class_name: str,
    level: int,
    *,
    look_ahead: bool = False,
    classes_index: dict[str, dict[str, Any]] | None = None,
) -> LevelSnapshot:
    classes = classes_index or load_classes()
    if class_name not in classes:
        raise KeyError(f"unknown class: {class_name}")

    class_row = classes[class_name]
    level_row = _get_level_row(class_row, level)
    gained = list(level_row.get("features_summary") or [])

    if look_ahead:
        visible: list[str] = []
        for n in range(level, MAX_LEVEL + 1):
            row = _get_level_row(class_row, n)
            for feature in row.get("features_summary") or []:
                tag = f"L{n}: {feature}"
                if tag not in visible:
                    visible.append(tag)
    else:
        visible = list(gained)

    return LevelSnapshot(
        class_name=class_name,
        level=level,
        proficiency_bonus=int(level_row.get("proficiency_bonus", 2)),
        gained_features=gained,
        visible_features=visible,
        spellcasting=level_row.get("spellcasting"),
    )


def level_up(
    class_name: str,
    current_level: int,
    *,
    look_ahead: bool = False,
    classes_index: dict[str, dict[str, Any]] | None = None,
) -> LevelSnapshot:
    if current_level >= MAX_LEVEL:
        raise ValueError("character is already at max level")
    return build_level_snapshot(
        class_name,
        current_level + 1,
        look_ahead=look_ahead,
        classes_index=classes_index,
    )
