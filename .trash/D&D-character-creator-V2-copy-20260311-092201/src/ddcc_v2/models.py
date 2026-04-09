"""Data model for level-1 SRD character data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ABILITIES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


@dataclass
class Character:
    name: str = ""
    level: int = 1
    alignment: str = "Neutral"
    species: str = "Human"
    char_class: str = "Fighter"
    background: str = "Acolyte"

    base_ability_scores: dict[str, int] = field(
        default_factory=lambda: {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8}
    )
    final_ability_scores: dict[str, int] = field(default_factory=lambda: {k: 10 for k in ABILITIES})
    ability_modifiers: dict[str, int] = field(default_factory=lambda: {k: 0 for k in ABILITIES})

    proficiency_bonus: int = 2
    saving_throw_proficiencies: list[str] = field(default_factory=list)
    skill_proficiencies: list[str] = field(default_factory=list)
    skill_bonuses: dict[str, int] = field(default_factory=dict)
    languages: list[str] = field(default_factory=list)

    size: str = "Medium"
    speed: int = 30
    max_hp: int = 1
    ac_baseline: int = 10
    initiative: int = 0
    passive_perception: int = 10

    selected_armor: str = ""
    equipment: list[str] = field(default_factory=list)
    attacks: list[str] = field(default_factory=list)

    spellcasting_ability: str | None = None
    spell_save_dc: int | None = None
    spell_attack_bonus: int | None = None
    known_spells: dict[str, list[str]] = field(default_factory=lambda: {"0": [], "1": []})

    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "alignment": self.alignment,
            "species": self.species,
            "char_class": self.char_class,
            "background": self.background,
            "base_ability_scores": self.base_ability_scores,
            "final_ability_scores": self.final_ability_scores,
            "ability_modifiers": self.ability_modifiers,
            "proficiency_bonus": self.proficiency_bonus,
            "saving_throw_proficiencies": self.saving_throw_proficiencies,
            "skill_proficiencies": self.skill_proficiencies,
            "skill_bonuses": self.skill_bonuses,
            "languages": self.languages,
            "size": self.size,
            "speed": self.speed,
            "max_hp": self.max_hp,
            "ac_baseline": self.ac_baseline,
            "initiative": self.initiative,
            "passive_perception": self.passive_perception,
            "selected_armor": self.selected_armor,
            "equipment": self.equipment,
            "attacks": self.attacks,
            "spellcasting_ability": self.spellcasting_ability,
            "spell_save_dc": self.spell_save_dc,
            "spell_attack_bonus": self.spell_attack_bonus,
            "known_spells": self.known_spells,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Character":
        char = cls()
        for key, value in data.items():
            if hasattr(char, key):
                setattr(char, key, value)

        for ability in ABILITIES:
            char.base_ability_scores.setdefault(ability, 10)
            char.final_ability_scores.setdefault(ability, char.base_ability_scores.get(ability, 10))
            char.ability_modifiers.setdefault(ability, 0)

        char.known_spells = {
            "0": list(char.known_spells.get("0", [])),
            "1": list(char.known_spells.get("1", [])),
        }

        if not isinstance(char.languages, list):
            char.languages = []
        if not isinstance(char.equipment, list):
            char.equipment = []
        if not isinstance(char.attacks, list):
            char.attacks = []

        return char
