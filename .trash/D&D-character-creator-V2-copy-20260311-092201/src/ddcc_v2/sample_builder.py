"""Sample character generation helpers."""

from __future__ import annotations

from .data_loader import index_by_name, load_dataset
from .models import Character
from .service import derive_character


def build_sample_character() -> Character:
    data = load_dataset()

    char = Character(
        name="Mira Dawnwhistle",
        alignment="Neutral Good",
        species="Human",
        char_class="Wizard",
        background="Sage",
        base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 15, "WIS": 12, "CHA": 10},
        equipment=["Quarterstaff", "Arcane Focus", "Scholar's Pack", "Spellbook", "Dagger"],
        attacks=["Quarterstaff", "Fire Bolt"],
    )

    skills = index_by_name(data["skills"])
    char.skill_proficiencies = ["Arcana", "History", "Investigation", "Insight"]
    char.known_spells = {
        "0": ["Fire Bolt", "Mage Hand", "Prestidigitation"],
        "1": ["Magic Missile", "Shield", "Mage Armor", "Detect Magic", "Sleep", "Burning Hands"],
    }

    return derive_character(char, data, selected_armor=None, skills_index=skills)
