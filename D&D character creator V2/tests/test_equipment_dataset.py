from ddcc_v2.data_loader import load_dataset


def test_equipment_sections_exist():
    equipment = load_dataset()["equipment"]
    required = ["armor", "weapons", "tools", "mounts_vehicles", "trade_goods", "adventuring_gear", "packs"]
    for section in required:
        assert section in equipment
        assert isinstance(equipment[section], list)
        assert equipment[section]


def test_armor_records_have_rich_and_compatibility_fields():
    armor = load_dataset()["equipment"]["armor"]
    rich_fields = {
        "name",
        "category",
        "armor_type",
        "base_ac",
        "dex_cap",
        "str_requirement",
        "stealth_disadvantage",
        "weight",
        "cost_gp",
        "description",
    }
    compatibility_fields = {"ac", "type"}

    for item in armor:
        assert rich_fields.issubset(item.keys()), f"Missing rich armor fields for {item.get('name')}"
        assert compatibility_fields.issubset(item.keys()), f"Missing compatibility armor fields for {item.get('name')}"


def test_weapons_have_rich_and_compatibility_fields():
    weapons = load_dataset()["equipment"]["weapons"]
    rich_fields = {
        "name",
        "category",
        "weapon_type",
        "damage_dice",
        "damage_type",
        "properties",
        "range_normal",
        "range_long",
        "weight",
        "cost_gp",
        "description",
    }
    compatibility_fields = {"damage", "properties_text"}

    for weapon in weapons:
        assert rich_fields.issubset(weapon.keys()), f"Missing rich weapon fields for {weapon.get('name')}"
        assert compatibility_fields.issubset(weapon.keys()), f"Missing compatibility weapon fields for {weapon.get('name')}"
        assert isinstance(weapon["properties"], list), f"Weapon properties must be a list: {weapon['name']}"
        assert isinstance(weapon["properties_text"], str), f"Weapon properties_text must be a string: {weapon['name']}"


def test_armor_and_weapon_coverage_constraints():
    equipment = load_dataset()["equipment"]
    armor = equipment["armor"]
    weapons = equipment["weapons"]

    assert any(item.get("armor_type") == "shield" for item in armor), "At least one shield is required"
    assert any(item.get("armor_type") == "heavy" and int(item.get("str_requirement", 0)) > 0 for item in armor), (
        "At least one heavy armor with STR requirement is required"
    )

    assert any(
        weapon.get("weapon_type") == "ranged"
        and weapon.get("range_normal") is not None
        and weapon.get("range_long") is not None
        for weapon in weapons
    ), "At least one ranged weapon with range values is required"


def test_pack_contents_are_structured_and_non_empty():
    packs = load_dataset()["equipment"]["packs"]
    for pack in packs:
        assert "contents" in pack, f"Pack missing contents: {pack.get('name')}"
        assert isinstance(pack["contents"], list), f"Pack contents must be a list: {pack.get('name')}"
        assert pack["contents"], f"Pack contents cannot be empty: {pack.get('name')}"
        for entry in pack["contents"]:
            assert isinstance(entry, dict)
            assert "item" in entry and isinstance(entry["item"], str) and entry["item"]
            assert "qty" in entry and isinstance(entry["qty"], int) and entry["qty"] > 0
