from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .leveling import MAX_LEVEL


@dataclass(frozen=True)
class BuilderState:
    class_name: str
    level: int
    look_ahead: bool


def _clamp_level(value: Any) -> int:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return 1
    return min(MAX_LEVEL, max(1, level))


def serialize_builder_state(state: BuilderState) -> dict[str, Any]:
    return {
        "builder": {
            "class_name": state.class_name,
            "level": _clamp_level(state.level),
            "look_ahead": bool(state.look_ahead),
        }
    }


def deserialize_builder_state(
    payload: dict[str, Any] | None,
    *,
    available_classes: Iterable[str],
) -> BuilderState:
    classes = list(available_classes)
    if not classes:
        raise ValueError("available_classes cannot be empty")

    default_class = classes[0]
    data = payload.get("builder", {}) if isinstance(payload, dict) else {}

    class_name = data.get("class_name", default_class)
    if class_name not in classes:
        class_name = default_class

    level = _clamp_level(data.get("level", 1))
    look_ahead = bool(data.get("look_ahead", False))

    return BuilderState(
        class_name=class_name,
        level=level,
        look_ahead=look_ahead,
    )
