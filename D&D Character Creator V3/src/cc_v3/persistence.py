from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .leveling import MAX_LEVEL


@dataclass(frozen=True)
class BuilderState:
    class_name: str
    level: int
    look_ahead: bool


@dataclass(frozen=True)
class AppShellState:
    title_text: str
    status_text: str
    active_tab: str


@dataclass(frozen=True)
class AppState:
    shell: AppShellState
    builder: BuilderState


def _clamp_level(value: Any) -> int:
    try:
        level = int(value)
    except (TypeError, ValueError):
        return 1
    return min(MAX_LEVEL, max(1, level))


def _coerce_text(value: Any, fallback: str) -> str:
    text = str(value).strip() if isinstance(value, str) else ""
    return text or fallback


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


def serialize_app_state(state: AppState) -> dict[str, Any]:
    payload = serialize_builder_state(state.builder)
    payload["shell"] = {
        "title_text": _coerce_text(state.shell.title_text, "D&D Character Creator V3"),
        "status_text": _coerce_text(state.shell.status_text, "Ready"),
        "active_tab": _coerce_text(state.shell.active_tab, "Builder"),
    }
    return payload


def deserialize_app_state(
    payload: dict[str, Any] | None,
    *,
    available_classes: Iterable[str],
    available_tabs: Iterable[str] = ("Builder", "Library"),
) -> AppState:
    tabs = [t for t in available_tabs if isinstance(t, str) and t.strip()]
    if not tabs:
        tabs = ["Builder"]

    data = payload.get("shell", {}) if isinstance(payload, dict) else {}

    active_tab = _coerce_text(data.get("active_tab"), tabs[0])
    if active_tab not in tabs:
        active_tab = tabs[0]

    shell = AppShellState(
        title_text=_coerce_text(data.get("title_text"), "D&D Character Creator V3"),
        status_text=_coerce_text(data.get("status_text"), "Ready"),
        active_tab=active_tab,
    )

    builder = deserialize_builder_state(payload, available_classes=available_classes)
    return AppState(shell=shell, builder=builder)
