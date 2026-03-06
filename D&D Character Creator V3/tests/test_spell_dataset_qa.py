import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "cc_v3" / "data"


def load_json(name):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def _spells_by_name(spells):
    return {spell["name"]: spell for spell in spells}


def test_spells_by_class_has_expected_level_buckets():
    spells_by_class = load_json("spells_by_class.json")
    expected_levels = {str(i) for i in range(10)}

    assert isinstance(spells_by_class, dict)
    assert spells_by_class, "spells_by_class.json should not be empty"

    for class_name, level_map in spells_by_class.items():
        assert set(level_map.keys()) == expected_levels, (
            f"{class_name} should define level buckets 0-9"
        )
        for level, spell_names in level_map.items():
            assert isinstance(spell_names, list), (
                f"{class_name} level {level} should map to a list of spell names"
            )


def test_levels_1_to_9_class_spell_references_match_spell_metadata():
    spells = load_json("spells.json")
    spells_by_class = load_json("spells_by_class.json")
    by_name = _spells_by_name(spells)

    missing = []
    level_mismatch = []
    class_mismatch = []

    for class_name, level_map in spells_by_class.items():
        for level in range(1, 10):
            for spell_name in level_map[str(level)]:
                spell = by_name.get(spell_name)
                if spell is None:
                    missing.append((class_name, level, spell_name))
                    continue
                if spell.get("level") != level:
                    level_mismatch.append(
                        (class_name, level, spell_name, spell.get("level"))
                    )
                if class_name not in spell.get("classes", []):
                    class_mismatch.append((class_name, level, spell_name))

    assert not missing, f"Unknown spell references: {missing}"
    assert not level_mismatch, f"Level mismatches found: {level_mismatch}"
    assert not class_mismatch, f"Class membership mismatches found: {class_mismatch}"


def test_levels_1_to_9_spell_metadata_is_consistent_and_bidirectional():
    spells = load_json("spells.json")
    spells_by_class = load_json("spells_by_class.json")

    invalid_levels = []
    missing_metadata = []
    reverse_mapping_gaps = []

    required_string_fields = [
        "name",
        "school",
        "casting_time",
        "range",
        "components",
        "duration",
        "rules_text",
        "description",
    ]

    for spell in spells:
        level = spell.get("level")
        name = spell.get("name", "<unknown>")

        if not isinstance(level, int) or not 0 <= level <= 9:
            invalid_levels.append((name, level))
            continue

        if 1 <= level <= 9:
            for field in required_string_fields:
                value = spell.get(field)
                if not isinstance(value, str) or not value.strip():
                    missing_metadata.append((name, field, value))

            classes = spell.get("classes")
            if not isinstance(classes, list) or not classes:
                missing_metadata.append((name, "classes", classes))
                continue

            for class_name in classes:
                if class_name not in spells_by_class:
                    reverse_mapping_gaps.append((name, class_name, level, "missing class key"))
                    continue
                if name not in spells_by_class[class_name][str(level)]:
                    reverse_mapping_gaps.append(
                        (name, class_name, level, "not present in spells_by_class")
                    )

    assert not invalid_levels, f"Spells with invalid levels found: {invalid_levels}"
    assert not missing_metadata, f"Metadata issues for levels 1-9: {missing_metadata}"
    assert not reverse_mapping_gaps, (
        "Bidirectional mapping gaps between spells.json and spells_by_class.json: "
        f"{reverse_mapping_gaps}"
    )
