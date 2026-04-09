"""Business logic for validation and derived stat computation."""

from __future__ import annotations

from typing import Any

from .calculations import (
    ability_modifier,
    calculate_armor_class,
    calculate_max_hp,
    calculate_passive_perception,
    calculate_spell_attack_bonus,
    calculate_spell_save_dc,
    proficiency_bonus,
)
from .data_loader import index_by_name
from .models import ABILITIES, Character


class ValidationError(ValueError):
    pass


def validate_ability_scores(scores: dict[str, int]) -> None:
    for ability in ABILITIES:
        value = int(scores.get(ability, 10))
        if value < 3 or value > 18:
            raise ValidationError(f"{ability} must be between 3 and 18 (got {value}).")


def validate_character_input(character: Character, data: dict[str, Any]) -> None:
    if not character.name.strip():
        raise ValidationError("Name is required.")

    classes = {c["name"] for c in data["classes"]}
    species = {s["name"] for s in data["species"]}
    backgrounds = {b["name"] for b in data["backgrounds"]}

    if character.char_class not in classes:
        raise ValidationError("Invalid class selection.")
    if character.species not in species:
        raise ValidationError("Invalid species selection.")
    if character.background not in backgrounds:
        raise ValidationError("Invalid background selection.")

    validate_ability_scores(character.base_ability_scores)


def derive_character(
    character: Character,
    data: dict[str, Any],
    selected_armor: dict[str, Any] | None,
    skills_index: dict[str, dict[str, Any]] | None = None,
) -> Character:
    classes = index_by_name(data["classes"])
    species = index_by_name(data["species"])
    backgrounds = index_by_name(data["backgrounds"])
    if skills_index is None:
        skills_index = index_by_name(data["skills"])

    class_def = classes[character.char_class]
    species_def = species[character.species]
    bg_def = backgrounds[character.background]

    final_scores: dict[str, int] = {}
    ability_mods: dict[str, int] = {}

    for ability in ABILITIES:
        base = int(character.base_ability_scores.get(ability, 10))
        bonus = int(species_def.get("ability_bonuses", {}).get(ability, 0))
        final = base + bonus
        final_scores[ability] = final
        ability_mods[ability] = ability_modifier(final)

    prof = proficiency_bonus(character.level)

    all_skill_profs = set(character.skill_proficiencies)
    for bg_skill in bg_def.get("skill_proficiencies", []):
        all_skill_profs.add(bg_skill)

    skill_bonuses: dict[str, int] = {}
    for skill in data["skills"]:
        key = skill["name"]
        ability = skill["ability"]
        bonus = ability_mods.get(ability, 0)
        if key in all_skill_profs:
            bonus += prof
        skill_bonuses[key] = bonus

    character.final_ability_scores = final_scores
    character.ability_modifiers = ability_mods
    character.proficiency_bonus = prof
    character.saving_throw_proficiencies = list(class_def.get("saving_throws", []))
    character.skill_proficiencies = sorted(all_skill_profs)
    character.skill_bonuses = skill_bonuses

    base_langs = list(species_def.get("languages", []))
    for lang in bg_def.get("languages", []):
        if lang not in base_langs:
            base_langs.append(lang)
    for lang in character.languages:
        if lang not in base_langs:
            base_langs.append(lang)
    character.languages = base_langs

    character.size = species_def.get("size", "Medium")
    character.speed = int(species_def.get("speed", 30))
    character.max_hp = calculate_max_hp(character.level, int(class_def.get("hit_die", 8)), ability_mods["CON"])
    character.ac_baseline = calculate_armor_class(ability_mods["DEX"], selected_armor)
    character.initiative = ability_mods["DEX"]
    character.passive_perception = calculate_passive_perception(skill_bonuses.get("Perception", ability_mods["WIS"]))

    spell_ability = class_def.get("spellcasting_ability")
    character.spellcasting_ability = spell_ability
    if spell_ability:
        cast_mod = ability_mods.get(spell_ability, 0)
        character.spell_save_dc = calculate_spell_save_dc(prof, cast_mod)
        character.spell_attack_bonus = calculate_spell_attack_bonus(prof, cast_mod)
    else:
        character.spell_save_dc = None
        character.spell_attack_bonus = None
        character.known_spells = {"0": [], "1": []}

    return character
