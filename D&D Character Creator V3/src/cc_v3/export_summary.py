from __future__ import annotations

from typing import Sequence

from .derived_combat import build_derived_combat_summary
from .persistence import (
    ABILITY_NAMES,
    CORE_SKILLS,
    AppState,
    BuilderState,
    compute_ability_modifiers,
    concise_equipment_line,
    concise_notes_line,
    concise_trait_line,
    normalize_skill_proficiencies,
)


def _first_n(values: Sequence[str], limit: int) -> str:
    if not values:
        return "None"
    head = list(values[:limit])
    suffix = f" (+{len(values) - limit} more)" if len(values) > limit else ""
    return ", ".join(head) + suffix


def _validation_issues(builder: BuilderState) -> list[str]:
    issues: list[str] = []
    if not builder.character_name:
        issues.append("missing name")
    if not builder.class_name:
        issues.append("missing class")
    if builder.level < 1:
        issues.append("invalid level")
    return issues


def format_character_export_summary(
    state: AppState,
    *,
    validation_issues: Sequence[str] | None = None,
) -> str:
    """Build a deterministic plain-text character summary from normalized app state."""

    builder = state.builder
    ability_mods = compute_ability_modifiers(builder.ability_scores)

    normalized_skills = normalize_skill_proficiencies(builder.skill_proficiencies)
    selected_core_skills = [skill for skill in CORE_SKILLS if normalized_skills[skill]]
    prepared_spells = builder.prepared_spells_text.splitlines() if builder.prepared_spells_text else []

    effective_issues = sorted(set(validation_issues)) if validation_issues is not None else _validation_issues(builder)
    validation_status = "OK" if not effective_issues else "; ".join(effective_issues)

    ability_text = ", ".join(
        f"{ability} {builder.ability_scores[ability]} ({ability_mods[ability]:+d})"
        for ability in ABILITY_NAMES
    )
    derived_combat_summary = build_derived_combat_summary(
        ability_scores=builder.ability_scores,
        skill_proficiencies=builder.skill_proficiencies,
        proficiency_bonus=max(2, 2 + ((max(1, builder.level) - 1) // 4)),
    )

    return "\n".join(
        [
            "Character Summary",
            f"Identity: {builder.character_name or 'Unnamed'} | {builder.race_species or 'Unspecified'} | {builder.background or 'Unspecified'} | {builder.alignment or 'Unspecified'}",
            f"Personality: Trait={concise_trait_line(builder.trait)} | Ideal={concise_trait_line(builder.ideal)} | Bond={concise_trait_line(builder.bond)} | Flaw={concise_trait_line(builder.flaw)}",
            f"Notes: {concise_notes_line(builder.character_notes)}",
            f"Class/Level: {builder.class_name} {builder.level}",
            f"Ability Scores: {ability_text}",
            f"Derived Combat: {derived_combat_summary}",
            f"Core Proficiencies: {_first_n(selected_core_skills, 4)} ({len(selected_core_skills)}/{len(CORE_SKILLS)})",
            f"Languages: {builder.languages or 'None'}",
            f"Equipment: {concise_equipment_line(builder.starting_gold, builder.inventory_text)}",
            f"Spell Highlights: {_first_n(prepared_spells, 3)}",
            f"Validation Status: {validation_status}",
        ]
    )
