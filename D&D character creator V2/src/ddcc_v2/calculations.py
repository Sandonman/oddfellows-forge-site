"""Core calculations for level-1 character mechanics."""

from __future__ import annotations

from typing import Optional


def ability_modifier(score: int) -> int:
    """Calculate 5e-style ability modifier."""
    return (int(score) - 10) // 2


def proficiency_bonus(level: int) -> int:
    """Calculate proficiency bonus by level."""
    lvl = max(1, int(level))
    return 2 + (lvl - 1) // 4


def format_bonus(value: int) -> str:
    return f"+{value}" if value >= 0 else str(value)


def calculate_max_hp(level: int, hit_die: int, con_mod: int) -> int:
    """At level 1, max HP is hit die max + CON modifier."""
    if level <= 1:
        return max(1, int(hit_die) + int(con_mod))
    return max(1, int(hit_die) + int(con_mod) + (level - 1) * (int(hit_die) // 2 + 1 + int(con_mod)))


def calculate_armor_class(dex_mod: int, armor_item: Optional[dict]) -> int:
    """Calculate baseline AC from selected armor or unarmored fallback."""
    if not armor_item:
        return 10 + int(dex_mod)

    base_ac = int(armor_item.get("ac", 10))
    armor_type = armor_item.get("type", "light").lower()

    if armor_type == "light":
        return base_ac + int(dex_mod)
    if armor_type == "medium":
        return base_ac + min(2, int(dex_mod))
    if armor_type == "heavy":
        return base_ac
    return base_ac + int(dex_mod)


def calculate_spell_save_dc(prof: int, casting_mod: int) -> int:
    return 8 + int(prof) + int(casting_mod)


def calculate_spell_attack_bonus(prof: int, casting_mod: int) -> int:
    return int(prof) + int(casting_mod)


def calculate_passive_perception(perception_bonus: int) -> int:
    return 10 + int(perception_bonus)
