from ddcc_v2.calculations import proficiency_bonus
from ddcc_v2.data_loader import load_dataset


def test_all_classes_have_level_1_to_20_progression():
    data = load_dataset()
    for cls in data["classes"]:
        progression = cls.get("level_progression")
        assert isinstance(progression, list), f"{cls['name']} missing level_progression list"
        assert len(progression) == 20, f"{cls['name']} progression should have 20 levels"

        levels = [row["level"] for row in progression]
        assert levels == list(range(1, 21)), f"{cls['name']} progression levels must be 1..20"

        for row in progression:
            lvl = row["level"]
            assert row["proficiency_bonus"] == proficiency_bonus(lvl), f"{cls['name']} has incorrect PB at level {lvl}"
            assert row.get("features_summary"), f"{cls['name']} missing feature summary at level {lvl}"


def test_spellcasting_progression_metadata_present_where_applicable():
    data = load_dataset()
    classes = {c["name"]: c for c in data["classes"]}

    for name in ["Bard", "Cleric", "Druid", "Sorcerer", "Wizard"]:
        for row in classes[name]["level_progression"]:
            spellcasting = row["spellcasting"]
            assert spellcasting["caster_type"] == "full"
            assert set(spellcasting["spell_slots"].keys()) == {str(i) for i in range(1, 10)}

    for name in ["Paladin", "Ranger"]:
        for row in classes[name]["level_progression"]:
            spellcasting = row["spellcasting"]
            assert spellcasting["caster_type"] == "half"
            assert set(spellcasting["spell_slots"].keys()) == {str(i) for i in range(1, 10)}

    for row in classes["Warlock"]["level_progression"]:
        spellcasting = row["spellcasting"]
        assert spellcasting["caster_type"] == "pact"
        assert "pact_slots" in spellcasting
        assert "pact_slot_level" in spellcasting

    for name in ["Barbarian", "Fighter", "Monk", "Rogue"]:
        for row in classes[name]["level_progression"]:
            assert row["spellcasting"] is None


def test_spells_cover_levels_0_to_9_and_include_rules_text():
    data = load_dataset()
    spells = data["spells"]

    levels_present = {spell["level"] for spell in spells}
    assert levels_present == set(range(10))

    for spell in spells:
        assert spell["classes"], f"{spell['name']} must include class eligibility"
        assert spell.get("rules_text"), f"{spell['name']} missing rules_text"


def test_spells_by_class_index_matches_spells_dataset():
    data = load_dataset()
    spells = data["spells"]
    grouped = data["spells_by_class"]

    for class_name, by_level in grouped.items():
        assert set(by_level.keys()) == {str(i) for i in range(10)}
        for level_key, names in by_level.items():
            level = int(level_key)
            expected = sorted(
                spell["name"] for spell in spells if spell["level"] == level and class_name in spell["classes"]
            )
            assert names == expected, f"{class_name} level {level} grouped spell index out of sync"
