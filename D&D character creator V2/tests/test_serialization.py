import json

from ddcc_v2.data_loader import load_dataset
from ddcc_v2.models import Character
from ddcc_v2.service import derive_character


def test_character_roundtrip(tmp_path):
    char = Character(
        name="Test Hero",
        species="Elf",
        char_class="Wizard",
        background="Sage",
        base_ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 15, "WIS": 12, "CHA": 10},
        skill_proficiencies=["Arcana", "Investigation"],
        known_spells={"0": ["Fire Bolt"], "1": ["Magic Missile"]},
    )

    data = load_dataset()
    derived = derive_character(char, data, selected_armor=None)

    p = tmp_path / "char.json"
    p.write_text(json.dumps(derived.to_dict(), indent=2), encoding="utf-8")

    loaded = Character.from_dict(json.loads(p.read_text(encoding="utf-8")))
    assert loaded.name == "Test Hero"
    assert loaded.char_class == "Wizard"
    assert loaded.final_ability_scores["INT"] >= 15
    assert loaded.spell_save_dc is not None


def test_derive_includes_background_skills_and_languages():
    data = load_dataset()
    char = Character(
        name="Milo",
        species="Human",
        char_class="Fighter",
        background="Soldier",
        base_ability_scores={"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8},
        skill_proficiencies=["Athletics", "Survival"],
        languages=["Dwarvish"],
    )

    derived = derive_character(char, data, selected_armor={"ac": 16, "type": "heavy"})
    assert "Intimidation" in derived.skill_proficiencies
    assert "Common" in derived.languages
    assert "Dwarvish" in derived.languages
    assert derived.ac_baseline == 16
