"""Domain models for character creation."""

from dataclasses import dataclass

from .data import ABILITIES


@dataclass
class Character:
    name: str
    level: int
    species: str
    char_class: str
    background: str
    ability_scores: dict[str, int]
    saving_throw_proficiencies: list[str]
    skill_proficiencies: list[str]


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def proficiency_bonus(level: int) -> int:
    return 2 + (max(level, 1) - 1) // 4


def format_bonus(value: int) -> str:
    return f"+{value}" if value >= 0 else str(value)


def apply_ability_bonuses(base_scores: dict[str, int], bonuses: dict[str, int]) -> dict[str, int]:
    final_scores = {ability: base_scores.get(ability, 10) for ability in ABILITIES}
    for ability, bonus in bonuses.items():
        final_scores[ability] = final_scores.get(ability, 10) + bonus
    return final_scores
