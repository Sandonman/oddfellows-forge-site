from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .leveling import MAX_LEVEL

ABILITY_NAMES: tuple[str, ...] = (
    "STR",
    "DEX",
    "CON",
    "INT",
    "WIS",
    "CHA",
)
DEFAULT_ABILITY_SCORE = 10
MIN_ABILITY_SCORE = 1
MAX_ABILITY_SCORE = 30

CORE_SKILLS: tuple[str, ...] = (
    "Acrobatics",
    "Arcana",
    "Athletics",
    "Perception",
)

ALIGNMENT_OPTIONS: tuple[str, ...] = (
    "Lawful Good",
    "Neutral Good",
    "Chaotic Good",
    "Lawful Neutral",
    "True Neutral",
    "Chaotic Neutral",
    "Lawful Evil",
    "Neutral Evil",
    "Chaotic Evil",
)


@dataclass(frozen=True)
class BuilderState:
    class_name: str
    level: int
    look_ahead: bool
    ability_scores: dict[str, int] = field(default_factory=dict)
    skill_proficiencies: dict[str, bool] = field(default_factory=dict)
    character_name: str = ""
    race_species: str = ""
    background: str = ""
    trait: str = ""
    ideal: str = ""
    bond: str = ""
    flaw: str = ""
    character_notes: str = ""
    alignment: str = ""
    languages: str = ""
    starting_gold: int = 0
    inventory_text: str = ""
    prepared_spells_text: str = ""


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


def normalize_ability_scores(payload: Any) -> dict[str, int]:
    source = payload if isinstance(payload, dict) else {}
    normalized: dict[str, int] = {}

    for ability in ABILITY_NAMES:
        raw = source.get(ability, DEFAULT_ABILITY_SCORE)
        try:
            score = int(raw)
        except (TypeError, ValueError):
            score = DEFAULT_ABILITY_SCORE
        normalized[ability] = min(MAX_ABILITY_SCORE, max(MIN_ABILITY_SCORE, score))

    return normalized


def normalize_skill_proficiencies(payload: Any) -> dict[str, bool]:
    source = payload if isinstance(payload, dict) else {}
    return {skill: bool(source.get(skill, False)) for skill in CORE_SKILLS}


def normalize_identity_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def normalize_alignment(value: Any) -> str:
    candidate = normalize_identity_text(value)
    return candidate if candidate in ALIGNMENT_OPTIONS else ""


def normalize_trait_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    lines = [line.strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_character_notes_text(value: Any) -> str:
    return normalize_trait_text(value)


def _normalize_csv_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    parts = [part.strip() for part in value.split(",")]
    deduped = list(dict.fromkeys(part for part in parts if part))
    return ", ".join(deduped)


def normalize_languages_text(value: Any) -> str:
    return _normalize_csv_text(value)


def normalize_starting_gold(value: Any) -> int:
    try:
        gold = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, gold)


def normalize_inventory_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    lines = [line.strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_prepared_spells_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    lines = [line.strip() for line in value.splitlines()]
    deduped = list(dict.fromkeys(line for line in lines if line))
    return "\n".join(deduped)


def normalize_prepared_spells_list(value: Any) -> list[str]:
    normalized_text = normalize_prepared_spells_text(value)
    return normalized_text.splitlines() if normalized_text else []


def _truncate_with_ellipsis(value: str, *, max_len: int) -> str:
    if max_len <= 0:
        return ""
    if len(value) <= max_len:
        return value
    if max_len == 1:
        return "…"
    return value[: max_len - 1].rstrip() + "…"


def concise_trait_line(value: Any, *, max_len: int = 40) -> str:
    normalized = normalize_trait_text(value)
    if not normalized:
        return "None"
    first_line = normalized.splitlines()[0]
    return _truncate_with_ellipsis(first_line, max_len=max_len)


def concise_notes_line(value: Any, *, max_len: int = 60) -> str:
    normalized = normalize_character_notes_text(value)
    if not normalized:
        return "None"
    first_line = normalized.splitlines()[0]
    return _truncate_with_ellipsis(first_line, max_len=max_len)


def concise_equipment_line(
    starting_gold: Any,
    inventory_text: Any,
    *,
    item_limit: int = 3,
    item_max_len: int = 24,
) -> str:
    normalized_gold = normalize_starting_gold(starting_gold)
    inventory_items = normalize_inventory_text(inventory_text).splitlines()
    if not inventory_items:
        return f"{normalized_gold} gp; no listed items"

    safe_item_limit = max(1, item_limit)
    visible_items = [
        _truncate_with_ellipsis(item, max_len=max(1, item_max_len))
        for item in inventory_items[:safe_item_limit]
    ]
    extra_count = max(0, len(inventory_items) - safe_item_limit)
    suffix = f", … (+{extra_count} more)" if extra_count else ""
    return f"{normalized_gold} gp; {len(inventory_items)} item(s): {', '.join(visible_items)}{suffix}"


def compute_ability_modifier(score: Any) -> int:
    try:
        value = int(score)
    except (TypeError, ValueError):
        value = DEFAULT_ABILITY_SCORE
    clamped = min(MAX_ABILITY_SCORE, max(MIN_ABILITY_SCORE, value))
    return (clamped - 10) // 2


def compute_ability_modifiers(payload: Any) -> dict[str, int]:
    normalized_scores = normalize_ability_scores(payload)
    return {
        ability: compute_ability_modifier(score)
        for ability, score in normalized_scores.items()
    }


def serialize_builder_state(state: BuilderState) -> dict[str, Any]:
    return {
        "builder": {
            "class_name": state.class_name,
            "level": _clamp_level(state.level),
            "look_ahead": bool(state.look_ahead),
            "ability_scores": normalize_ability_scores(state.ability_scores),
            "skill_proficiencies": normalize_skill_proficiencies(state.skill_proficiencies),
            "character_name": normalize_identity_text(state.character_name),
            "race_species": normalize_identity_text(state.race_species),
            "background": normalize_identity_text(state.background),
            "trait": normalize_trait_text(state.trait),
            "ideal": normalize_trait_text(state.ideal),
            "bond": normalize_trait_text(state.bond),
            "flaw": normalize_trait_text(state.flaw),
            "character_notes": normalize_character_notes_text(state.character_notes),
            "alignment": normalize_alignment(state.alignment),
            "languages": normalize_languages_text(state.languages),
            "starting_gold": normalize_starting_gold(state.starting_gold),
            "inventory_text": normalize_inventory_text(state.inventory_text),
            "prepared_spells_text": normalize_prepared_spells_text(state.prepared_spells_text),
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
    if not isinstance(data, dict):
        data = {}

    class_name = data.get("class_name", default_class)
    if class_name not in classes:
        class_name = default_class

    level = _clamp_level(data.get("level", 1))
    look_ahead = bool(data.get("look_ahead", False))
    ability_scores = normalize_ability_scores(data.get("ability_scores", {}))
    skill_proficiencies = normalize_skill_proficiencies(data.get("skill_proficiencies", {}))
    character_name = normalize_identity_text(data.get("character_name", ""))
    race_species = normalize_identity_text(data.get("race_species", ""))
    background = normalize_identity_text(data.get("background", ""))
    trait = normalize_trait_text(data.get("trait", ""))
    ideal = normalize_trait_text(data.get("ideal", ""))
    bond = normalize_trait_text(data.get("bond", ""))
    flaw = normalize_trait_text(data.get("flaw", ""))
    character_notes = normalize_character_notes_text(data.get("character_notes", ""))
    alignment = normalize_alignment(data.get("alignment", ""))
    languages = normalize_languages_text(data.get("languages", ""))
    starting_gold = normalize_starting_gold(data.get("starting_gold", 0))
    inventory_text = normalize_inventory_text(data.get("inventory_text", ""))
    prepared_spells_text = normalize_prepared_spells_text(data.get("prepared_spells_text", ""))

    return BuilderState(
        class_name=class_name,
        level=level,
        look_ahead=look_ahead,
        ability_scores=ability_scores,
        skill_proficiencies=skill_proficiencies,
        character_name=character_name,
        race_species=race_species,
        background=background,
        trait=trait,
        ideal=ideal,
        bond=bond,
        flaw=flaw,
        character_notes=character_notes,
        alignment=alignment,
        languages=languages,
        starting_gold=starting_gold,
        inventory_text=inventory_text,
        prepared_spells_text=prepared_spells_text,
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
    if not isinstance(data, dict):
        data = {}

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


def _load_json_object(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ValueError("Imported payload must be a JSON object")
    return data


def export_builder_payload_json(
    payload: dict[str, Any] | None,
    *,
    available_classes: Iterable[str],
) -> str:
    normalized = serialize_builder_state(
        deserialize_builder_state(payload, available_classes=available_classes)
    )
    return json.dumps(normalized, indent=2, sort_keys=True) + "\n"


def import_builder_payload_json(
    text: str,
    *,
    available_classes: Iterable[str],
) -> dict[str, Any]:
    payload = _load_json_object(text)
    return serialize_builder_state(
        deserialize_builder_state(payload, available_classes=available_classes)
    )


def export_app_payload_json(
    payload: dict[str, Any] | None,
    *,
    available_classes: Iterable[str],
    available_tabs: Iterable[str] = ("Builder", "Library"),
) -> str:
    normalized = serialize_app_state(
        deserialize_app_state(
            payload,
            available_classes=available_classes,
            available_tabs=available_tabs,
        )
    )
    return json.dumps(normalized, indent=2, sort_keys=True) + "\n"


def import_app_payload_json(
    text: str,
    *,
    available_classes: Iterable[str],
    available_tabs: Iterable[str] = ("Builder", "Library"),
) -> dict[str, Any]:
    payload = _load_json_object(text)
    return serialize_app_state(
        deserialize_app_state(
            payload,
            available_classes=available_classes,
            available_tabs=available_tabs,
        )
    )


def _canonical_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy payload into a deterministic JSON-compatible structure."""

    return json.loads(json.dumps(payload, sort_keys=True))


def push_builder_undo_checkpoint(
    checkpoints: Iterable[dict[str, Any]] | None,
    payload: dict[str, Any] | None,
    *,
    available_classes: Iterable[str],
    capacity: int,
) -> tuple[dict[str, Any], ...]:
    """Normalize builder payload, then push it onto the undo stack."""

    normalized = serialize_builder_state(
        deserialize_builder_state(payload, available_classes=available_classes)
    )
    return push_undo_checkpoint(checkpoints, normalized, capacity=capacity)


def push_app_undo_checkpoint(
    checkpoints: Iterable[dict[str, Any]] | None,
    payload: dict[str, Any] | None,
    *,
    available_classes: Iterable[str],
    available_tabs: Iterable[str] = ("Builder", "Library"),
    capacity: int,
) -> tuple[dict[str, Any], ...]:
    """Normalize app payload, then push it onto the undo stack."""

    normalized = serialize_app_state(
        deserialize_app_state(
            payload,
            available_classes=available_classes,
            available_tabs=available_tabs,
        )
    )
    return push_undo_checkpoint(checkpoints, normalized, capacity=capacity)


def push_undo_checkpoint(
    checkpoints: Iterable[dict[str, Any]] | None,
    payload: dict[str, Any],
    *,
    capacity: int,
) -> tuple[dict[str, Any], ...]:
    """Push a canonical checkpoint and trim stack length to capacity."""

    limit = max(1, int(capacity))
    stack = [
        _canonical_snapshot(checkpoint)
        for checkpoint in (checkpoints or ())
        if isinstance(checkpoint, dict)
    ]
    stack.append(_canonical_snapshot(payload))
    return tuple(stack[-limit:])


def pop_undo_checkpoint(
    checkpoints: Iterable[dict[str, Any]] | None,
) -> tuple[dict[str, Any] | None, tuple[dict[str, Any], ...]]:
    """Pop the newest checkpoint and return it with remaining stack."""

    stack = [
        _canonical_snapshot(checkpoint)
        for checkpoint in (checkpoints or ())
        if isinstance(checkpoint, dict)
    ]
    if not stack:
        return None, ()
    restored = stack.pop()
    return restored, tuple(stack)


def summarize_release_candidate_readiness(
    payload: dict[str, Any] | None,
    *,
    available_classes: Iterable[str],
    available_tabs: Iterable[str] = ("Builder", "Library"),
) -> dict[str, Any]:
    """Return deterministic release-readiness checks for a canonical app payload."""

    classes = [item for item in available_classes if isinstance(item, str) and item.strip()]
    if not classes:
        raise ValueError("available_classes cannot be empty")

    tabs = [item for item in available_tabs if isinstance(item, str) and item.strip()]
    if not tabs:
        tabs = ["Builder"]

    raw_payload = payload if isinstance(payload, dict) else {}
    raw_shell = raw_payload.get("shell") if isinstance(raw_payload.get("shell"), dict) else {}
    raw_builder = raw_payload.get("builder") if isinstance(raw_payload.get("builder"), dict) else {}

    normalized_state = deserialize_app_state(
        raw_payload,
        available_classes=classes,
        available_tabs=tabs,
    )
    normalized_payload = serialize_app_state(normalized_state)

    identity_fields = (
        normalized_state.builder.character_name,
        normalized_state.builder.race_species,
        normalized_state.builder.background,
        normalized_state.builder.alignment,
    )
    identity_complete = all(identity_fields)

    raw_class_name = raw_builder.get("class_name")
    raw_level = raw_builder.get("level")
    try:
        raw_level_int = int(raw_level)
    except (TypeError, ValueError):
        raw_level_int = None

    class_level_valid = (
        isinstance(raw_class_name, str)
        and raw_class_name in set(classes)
        and raw_level_int is not None
        and 1 <= raw_level_int <= MAX_LEVEL
    )

    ability_normalized = (
        raw_builder.get("ability_scores") == normalize_ability_scores(raw_builder.get("ability_scores"))
    )

    notes_or_personality_present = any(
        (
            normalized_state.builder.trait,
            normalized_state.builder.ideal,
            normalized_state.builder.bond,
            normalized_state.builder.flaw,
            normalized_state.builder.character_notes,
        )
    )

    checkpoint_safe_payload_shape = (
        raw_payload == normalized_payload
        and set(raw_payload) == {"shell", "builder"}
        and isinstance(raw_shell, dict)
        and isinstance(raw_builder, dict)
    )

    checks = [
        {
            "key": "identity_complete",
            "ok": identity_complete,
            "detail": (
                "Identity fields complete"
                if identity_complete
                else "Missing one or more identity fields (name/species/background/alignment)"
            ),
        },
        {
            "key": "class_level_valid",
            "ok": class_level_valid,
            "detail": (
                "Class and level are valid"
                if class_level_valid
                else f"Class/level must be within available classes and level 1-{MAX_LEVEL}"
            ),
        },
        {
            "key": "ability_normalized",
            "ok": ability_normalized,
            "detail": (
                "Ability scores already canonical"
                if ability_normalized
                else "Ability scores require normalization"
            ),
        },
        {
            "key": "notes_or_personality_present",
            "ok": notes_or_personality_present,
            "detail": (
                "Notes/personality content present"
                if notes_or_personality_present
                else "Add at least one personality field or character notes"
            ),
        },
        {
            "key": "checkpoint_safe_payload_shape",
            "ok": checkpoint_safe_payload_shape,
            "detail": (
                "Payload is canonical and checkpoint-safe"
                if checkpoint_safe_payload_shape
                else "Payload differs from canonical app shape"
            ),
        },
    ]

    return {
        "ready": all(check["ok"] for check in checks),
        "checks": checks,
    }


def summarize_app_payload_changes(
    previous_payload: dict[str, Any] | None,
    current_payload: dict[str, Any] | None,
    *,
    available_classes: Iterable[str],
    available_tabs: Iterable[str] = ("Builder", "Library"),
) -> list[str]:
    """Return deterministic human-readable change lines between two app payloads."""

    previous = deserialize_app_state(
        previous_payload,
        available_classes=available_classes,
        available_tabs=available_tabs,
    )
    current = deserialize_app_state(
        current_payload,
        available_classes=available_classes,
        available_tabs=available_tabs,
    )

    def _fmt_identity(state: BuilderState) -> str:
        return " | ".join(
            (
                state.character_name or "(unnamed)",
                state.race_species or "(unspecified species)",
                state.background or "(unspecified background)",
                state.alignment or "(unspecified alignment)",
            )
        )

    def _fmt_skills(state: BuilderState) -> str:
        selected = [skill for skill in CORE_SKILLS if state.skill_proficiencies.get(skill, False)]
        return ", ".join(selected) if selected else "None"

    def _csv_items(value: str) -> list[str]:
        return [part.strip() for part in value.split(",") if part.strip()]

    def _line_items(value: str) -> list[str]:
        return [line.strip() for line in value.splitlines() if line.strip()]

    def _added_removed(before: list[str], after: list[str]) -> str:
        removed = sorted(set(before) - set(after))
        added = sorted(set(after) - set(before))
        parts: list[str] = []
        if removed:
            parts.append(f"removed [{', '.join(removed)}]")
        if added:
            parts.append(f"added [{', '.join(added)}]")
        return "; ".join(parts)

    lines: list[str] = []

    if _fmt_identity(previous.builder) != _fmt_identity(current.builder):
        lines.append(f"Identity: {_fmt_identity(previous.builder)} -> {_fmt_identity(current.builder)}")

    personality_labels = (
        ("Trait", previous.builder.trait, current.builder.trait),
        ("Ideal", previous.builder.ideal, current.builder.ideal),
        ("Bond", previous.builder.bond, current.builder.bond),
        ("Flaw", previous.builder.flaw, current.builder.flaw),
        ("Character Notes", previous.builder.character_notes, current.builder.character_notes),
    )
    for label, before, after in personality_labels:
        if before != after:
            lines.append(f"{label}: {(before or 'None')} -> {(after or 'None')}")

    if (
        previous.builder.class_name != current.builder.class_name
        or previous.builder.level != current.builder.level
        or previous.builder.look_ahead != current.builder.look_ahead
    ):
        lines.append(
            "Class/Level: "
            f"{previous.builder.class_name} {previous.builder.level}"
            f" (look-ahead={'on' if previous.builder.look_ahead else 'off'})"
            " -> "
            f"{current.builder.class_name} {current.builder.level}"
            f" (look-ahead={'on' if current.builder.look_ahead else 'off'})"
        )

    ability_changes = [
        f"{ability} {previous.builder.ability_scores[ability]}→{current.builder.ability_scores[ability]}"
        for ability in ABILITY_NAMES
        if previous.builder.ability_scores[ability] != current.builder.ability_scores[ability]
    ]
    if ability_changes:
        lines.append("Ability Scores: " + "; ".join(ability_changes))

    if _fmt_skills(previous.builder) != _fmt_skills(current.builder):
        lines.append(f"Skills: {_fmt_skills(previous.builder)} -> {_fmt_skills(current.builder)}")

    previous_languages = _csv_items(previous.builder.languages)
    current_languages = _csv_items(current.builder.languages)
    if previous_languages != current_languages:
        diff = _added_removed(previous_languages, current_languages)
        if diff:
            lines.append(f"Languages: {diff}")
        else:
            lines.append(
                "Languages: "
                f"{', '.join(previous_languages) if previous_languages else 'None'}"
                " -> "
                f"{', '.join(current_languages) if current_languages else 'None'}"
            )

    previous_equipment = _line_items(previous.builder.inventory_text)
    current_equipment = _line_items(current.builder.inventory_text)
    if previous_equipment != current_equipment:
        diff = _added_removed(previous_equipment, current_equipment)
        if diff:
            lines.append(f"Equipment: {diff}")
        else:
            lines.append(
                "Equipment order changed: "
                f"{len(previous_equipment)} items -> {len(current_equipment)} items"
            )

    previous_spells = _line_items(previous.builder.prepared_spells_text)
    current_spells = _line_items(current.builder.prepared_spells_text)
    if previous_spells != current_spells:
        diff = _added_removed(previous_spells, current_spells)
        if diff:
            lines.append(f"Spells: {diff}")
        else:
            lines.append(
                "Spells order changed: "
                f"{len(previous_spells)} entries -> {len(current_spells)} entries"
            )

    if previous.builder.starting_gold != current.builder.starting_gold:
        lines.append(f"Gold: {previous.builder.starting_gold} -> {current.builder.starting_gold}")

    if previous.shell.status_text != current.shell.status_text:
        lines.append(f"Status: {previous.shell.status_text} -> {current.shell.status_text}")

    if previous.shell.active_tab != current.shell.active_tab:
        lines.append(f"Active Tab: {previous.shell.active_tab} -> {current.shell.active_tab}")

    return lines


DEFAULT_STATE_PATH = Path("outputs") / "v3_last_state.json"


def write_state_payload(path: Path | str, payload: dict[str, Any]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return target


def read_state_payload(path: Path | str) -> dict[str, Any]:
    target = Path(path)
    with target.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("State file payload must be a JSON object")
    return data
