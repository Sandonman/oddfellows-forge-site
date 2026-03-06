import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "cc_v3" / "data"


def load_json(name: str):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def test_monsters_schema_basics():
    monsters = load_json("monsters.json")

    assert isinstance(monsters, list)
    assert monsters, "monsters.json should not be empty"

    required_keys = {
        "name",
        "size",
        "type",
        "armor_class",
        "hit_points",
        "speed",
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    }

    for monster in monsters:
        assert isinstance(monster, dict)
        missing = required_keys - set(monster.keys())
        assert not missing, f"Monster missing keys: {missing}"

        assert isinstance(monster["name"], str) and monster["name"].strip()
        assert isinstance(monster["size"], str) and monster["size"].strip()
        assert isinstance(monster["type"], str) and monster["type"].strip()

        assert isinstance(monster["armor_class"], int)
        assert isinstance(monster["hit_points"], int)
        assert isinstance(monster["speed"], dict)

        for stat in [
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
        ]:
            assert isinstance(monster[stat], int), f"{monster['name']} has non-int {stat}"


@pytest.mark.parametrize(
    "section,required_keys",
    [
        ("armor", {"name", "category", "base_ac", "weight", "cost_gp"}),
        (
            "weapons",
            {"name", "category", "damage_dice", "damage_type", "weight", "cost_gp"},
        ),
        ("tools", {"name", "category", "cost_gp"}),
    ],
)
def test_equipment_section_schema_basics(section, required_keys):
    equipment = load_json("equipment.json")

    assert isinstance(equipment, dict)
    assert section in equipment, f"equipment.json missing section: {section}"

    items = equipment[section]
    assert isinstance(items, list)
    assert items, f"equipment section {section} should not be empty"

    for item in items:
        assert isinstance(item, dict)
        missing = required_keys - set(item.keys())
        assert not missing, f"{section} item missing keys: {missing}"
        assert isinstance(item["name"], str) and item["name"].strip()


def test_equipment_packs_contents_schema_basics():
    equipment = load_json("equipment.json")

    assert "packs" in equipment
    packs = equipment["packs"]
    assert isinstance(packs, list)
    assert packs, "packs section should not be empty"

    for pack in packs:
        assert isinstance(pack, dict)
        assert "name" in pack
        assert "contents" in pack
        assert isinstance(pack["name"], str) and pack["name"].strip()
        assert isinstance(pack["contents"], list)

        for entry in pack["contents"]:
            assert isinstance(entry, dict)
            assert "item" in entry
            assert "qty" in entry
            assert isinstance(entry["item"], str) and entry["item"].strip()
            assert isinstance(entry["qty"], int)
