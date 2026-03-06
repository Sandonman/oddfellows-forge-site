from pathlib import Path

from cc_v3.persistence import (
    AppShellState,
    AppState,
    BuilderState,
    DEFAULT_STATE_PATH,
    compute_ability_modifier,
    compute_ability_modifiers,
    deserialize_app_state,
    deserialize_builder_state,
    export_app_payload_json,
    export_builder_payload_json,
    import_app_payload_json,
    import_builder_payload_json,
    normalize_alignment,
    normalize_character_notes_text,
    normalize_identity_text,
    normalize_prepared_spells_list,
    normalize_prepared_spells_text,
    normalize_trait_text,
    read_state_payload,
    serialize_app_state,
    serialize_builder_state,
    write_state_payload,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]
ABILITY_SCORES = {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8}
SKILL_PROFICIENCIES = {
    "Acrobatics": True,
    "Arcana": False,
    "Athletics": True,
    "Perception": False,
}


def test_compute_ability_modifier_uses_5e_formula_with_clamping():
    assert compute_ability_modifier(1) == -5
    assert compute_ability_modifier(8) == -1
    assert compute_ability_modifier(9) == -1
    assert compute_ability_modifier(10) == 0
    assert compute_ability_modifier(11) == 0
    assert compute_ability_modifier(12) == 1
    assert compute_ability_modifier(30) == 10
    assert compute_ability_modifier(99) == 10
    assert compute_ability_modifier("x") == 0


def test_compute_ability_modifiers_normalizes_scores_before_math():
    mods = compute_ability_modifiers({"STR": 99, "DEX": -3, "CON": "x", "INT": 12})

    assert mods == {
        "STR": 10,
        "DEX": -5,
        "CON": 0,
        "INT": 1,
        "WIS": 0,
        "CHA": 0,
    }


def test_identity_normalizers_trim_text_and_enforce_alignment_options():
    assert normalize_identity_text("  Elora  ") == "Elora"
    assert normalize_identity_text(None) == ""
    assert normalize_alignment("Neutral Good") == "Neutral Good"
    assert normalize_alignment("  Neutral Good ") == "Neutral Good"
    assert normalize_alignment("Chaotic Helpful") == ""


def test_builder_state_round_trip_preserves_core_builder_fields():
    state = BuilderState(
        class_name="Wizard",
        level=7,
        look_ahead=True,
        ability_scores=ABILITY_SCORES,
        skill_proficiencies=SKILL_PROFICIENCIES,
        languages="Common, Elvish",
        starting_gold=15,
        inventory_text="Rope\nTorch",
    )

    payload = serialize_builder_state(state)
    restored = deserialize_builder_state(payload, available_classes=CLASSES)

    assert restored == state


def test_deserialize_builder_state_clamps_and_falls_back_safely():
    payload = {
        "builder": {
            "class_name": "Unknown",
            "level": 99,
            "look_ahead": 1,
            "ability_scores": {"STR": 99, "DEX": -10, "CON": "x"},
            "skill_proficiencies": {"Acrobatics": 1, "Arcana": "", "Perception": True},
            "languages": " Common, , Draconic ,",
            "starting_gold": -99,
            "inventory_text": " Rope \n\n Torch\n",
        }
    }

    restored = deserialize_builder_state(payload, available_classes=CLASSES)

    assert restored.class_name == "Cleric"
    assert restored.level == 20
    assert restored.look_ahead is True
    assert restored.ability_scores == {
        "STR": 30,
        "DEX": 1,
        "CON": 10,
        "INT": 10,
        "WIS": 10,
        "CHA": 10,
    }
    assert restored.skill_proficiencies == {
        "Acrobatics": True,
        "Arcana": False,
        "Athletics": False,
        "Perception": True,
    }
    assert restored.character_name == ""
    assert restored.race_species == ""
    assert restored.background == ""
    assert restored.alignment == ""
    assert restored.languages == "Common, Draconic"
    assert restored.starting_gold == 0
    assert restored.inventory_text == "Rope\nTorch"


def test_deserialize_builder_state_normalizes_identity_fields():
    payload = {
        "builder": {
            "class_name": "Wizard",
            "level": 2,
            "character_name": "  Elora  ",
            "race_species": "  Elf ",
            "background": " Sage  ",
            "alignment": "Chaotic Helpful",
        }
    }

    restored = deserialize_builder_state(payload, available_classes=CLASSES)

    assert restored.character_name == "Elora"
    assert restored.race_species == "Elf"
    assert restored.background == "Sage"
    assert restored.alignment == ""


def test_personality_text_normalization_is_deterministic_for_whitespace_and_blank_values():
    assert normalize_trait_text(None) == ""
    assert normalize_trait_text("   ") == ""
    assert normalize_trait_text("  Keeps notes.  \n\n   Always plans ahead.   \n") == "Keeps notes.\nAlways plans ahead."


def test_character_notes_normalization_trims_and_drops_blank_only_content():
    assert normalize_character_notes_text(None) == ""
    assert normalize_character_notes_text("   \n\n  ") == ""
    assert normalize_character_notes_text("  Session goals  \n\n   Bring rope.  \n") == "Session goals\nBring rope."


def test_app_state_round_trip_preserves_shell_and_builder_fields():
    state = AppState(
        shell=AppShellState(
            title_text="Campaign: Icewind Dale",
            status_text="Autosave pending",
            active_tab="Library",
        ),
        builder=BuilderState(
            class_name="Wizard",
            level=5,
            look_ahead=False,
            ability_scores=ABILITY_SCORES,
            skill_proficiencies=SKILL_PROFICIENCIES,
            languages="Common, Elvish",
            starting_gold=25,
            inventory_text="Spellbook\nInk",
        ),
    )

    payload = serialize_app_state(state)
    restored = deserialize_app_state(
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert restored == state


def test_deserialize_app_state_clamps_and_falls_back_safely():
    payload = {
        "shell": {
            "title_text": "",
            "status_text": "",
            "active_tab": "Unknown tab",
        },
        "builder": {
            "class_name": "Nope",
            "level": -12,
            "look_ahead": 1,
            "ability_scores": {
                "STR": "18",
                "DEX": 999,
                "CON": -9,
                "INT": None,
                "WIS": "bad",
            },
            "skill_proficiencies": {"Athletics": 1},
            "languages": " , Giant, Common ",
            "starting_gold": "-4",
            "inventory_text": " Shield\n\n Rations ",
        },
    }

    restored = deserialize_app_state(
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert restored.shell.title_text == "D&D Character Creator V3"
    assert restored.shell.status_text == "Ready"
    assert restored.shell.active_tab == "Builder"
    assert restored.builder == BuilderState(
        class_name="Cleric",
        level=1,
        look_ahead=True,
        ability_scores={"STR": 18, "DEX": 30, "CON": 1, "INT": 10, "WIS": 10, "CHA": 10},
        skill_proficiencies={
            "Acrobatics": False,
            "Arcana": False,
            "Athletics": True,
            "Perception": False,
        },
        languages="Giant, Common",
        starting_gold=0,
        inventory_text="Shield\nRations",
    )


def test_app_state_round_trip_preserves_builder_ability_scores_from_shell_payload():
    payload = {
        "shell": {
            "title_text": "Campaign: Spelljammer",
            "status_text": "Saved",
            "active_tab": "Builder",
        },
        "builder": {
            "class_name": "Fighter",
            "level": 9,
            "look_ahead": False,
            "ability_scores": {"STR": 17, "DEX": 16, "CON": 15, "INT": 12, "WIS": 11, "CHA": 8},
            "skill_proficiencies": {"Athletics": True, "Perception": True},
            "languages": "Common, Dwarvish",
            "starting_gold": 33,
            "inventory_text": "Bedroll\nRope",
        },
    }

    restored = deserialize_app_state(
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    reserialized = serialize_app_state(restored)
    restored_again = deserialize_app_state(
        reserialized,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert restored_again.builder.ability_scores == {"STR": 17, "DEX": 16, "CON": 15, "INT": 12, "WIS": 11, "CHA": 8}
    assert restored_again.builder.skill_proficiencies == {
        "Acrobatics": False,
        "Arcana": False,
        "Athletics": True,
        "Perception": True,
    }
    assert restored_again.builder.languages == "Common, Dwarvish"
    assert restored_again.builder.starting_gold == 33
    assert restored_again.builder.inventory_text == "Bedroll\nRope"
    assert restored_again == restored


def test_builder_state_round_trip_normalizes_mixed_payload_deterministically_across_sections():
    mixed_payload = {
        "builder": {
            "class_name": "Wizard",
            "level": 999,
            "look_ahead": 1,
            "ability_scores": {
                "STR": 999,
                "DEX": -12,
                "CON": "18",
                "INT": None,
                "WIS": "bad",
                "CHA": 9,
            },
            "skill_proficiencies": {
                "Acrobatics": "yes",
                "Arcana": 0,
                "Athletics": 2,
                "Perception": "",
            },
            "languages": " Common, Elvish, Common,  Dwarvish ,",
            "starting_gold": "150",
            "inventory_text": "  Rope  \n\n Torch\n  Rations  ",
        }
    }

    restored = deserialize_builder_state(mixed_payload, available_classes=CLASSES)
    serialized_once = serialize_builder_state(restored)
    restored_again = deserialize_builder_state(serialized_once, available_classes=CLASSES)
    serialized_twice = serialize_builder_state(restored_again)

    assert restored.level == 20
    assert restored.ability_scores == {
        "STR": 30,
        "DEX": 1,
        "CON": 18,
        "INT": 10,
        "WIS": 10,
        "CHA": 9,
    }
    assert restored.skill_proficiencies == {
        "Acrobatics": True,
        "Arcana": False,
        "Athletics": True,
        "Perception": False,
    }
    assert restored.languages == "Common, Elvish, Dwarvish"
    assert restored.starting_gold == 150
    assert restored.inventory_text == "Rope\nTorch\nRations"

    assert restored_again == restored
    assert serialized_twice == serialized_once


def test_app_state_round_trip_normalizes_and_preserves_builder_equipment_with_edge_inputs():
    payload = {
        "shell": {
            "title_text": "Campaign: Integration",
            "status_text": "Dirty",
            "active_tab": "Builder",
        },
        "builder": {
            "class_name": "Fighter",
            "level": 0,
            "look_ahead": "",
            "ability_scores": {"STR": -5, "DEX": 35, "CON": "x", "INT": 7, "WIS": 10, "CHA": 11},
            "skill_proficiencies": {"Acrobatics": 1, "Arcana": "", "Athletics": "on", "Perception": 0},
            "languages": " Common, , Common , Giant ",
            "starting_gold": -999,
            "inventory_text": "  Shield\n\nLongsword  \n  "
        },
    }

    restored = deserialize_app_state(
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    reserialized = serialize_app_state(restored)
    restored_again = deserialize_app_state(
        reserialized,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert restored.builder.ability_scores == {"STR": 1, "DEX": 30, "CON": 10, "INT": 7, "WIS": 10, "CHA": 11}
    assert restored.builder.skill_proficiencies == {
        "Acrobatics": True,
        "Arcana": False,
        "Athletics": True,
        "Perception": False,
    }
    assert restored.builder.languages == "Common, Giant"
    assert restored.builder.starting_gold == 0
    assert restored.builder.inventory_text == "Shield\nLongsword"
    assert restored_again == restored


def test_prepared_spells_normalization_helpers_dedupe_and_strip_blanks():
    value = "  Mage Armor  \n\nShield\nMage Armor\n  "

    assert normalize_prepared_spells_text(value) == "Mage Armor\nShield"
    assert normalize_prepared_spells_list(value) == ["Mage Armor", "Shield"]


def test_builder_state_round_trip_preserves_prepared_spells_text():
    state = BuilderState(
        class_name="Wizard",
        level=5,
        look_ahead=False,
        ability_scores=ABILITY_SCORES,
        skill_proficiencies=SKILL_PROFICIENCIES,
        languages="Common",
        starting_gold=10,
        inventory_text="Spellbook",
        prepared_spells_text=" Mage Armor\n\nShield\nMage Armor ",
    )

    payload = serialize_builder_state(state)
    restored = deserialize_builder_state(payload, available_classes=CLASSES)

    assert payload["builder"]["prepared_spells_text"] == "Mage Armor\nShield"
    assert restored.prepared_spells_text == "Mage Armor\nShield"


def test_builder_state_round_trip_preserves_and_normalizes_traits_block():
    state = BuilderState(
        class_name="Wizard",
        level=5,
        look_ahead=False,
        ability_scores=ABILITY_SCORES,
        skill_proficiencies=SKILL_PROFICIENCIES,
        trait="  Curious about ancient ruins.  \n\n",
        ideal="  Knowledge should be shared. ",
        bond="  My mentor's staff  ",
        flaw="  I trust old books too much.\n",
    )

    payload = serialize_builder_state(state)
    restored = deserialize_builder_state(payload, available_classes=CLASSES)

    assert payload["builder"]["trait"] == "Curious about ancient ruins."
    assert payload["builder"]["ideal"] == "Knowledge should be shared."
    assert payload["builder"]["bond"] == "My mentor's staff"
    assert payload["builder"]["flaw"] == "I trust old books too much."
    assert restored.trait == "Curious about ancient ruins."
    assert restored.ideal == "Knowledge should be shared."
    assert restored.bond == "My mentor's staff"
    assert restored.flaw == "I trust old books too much."


def test_builder_state_round_trip_preserves_and_normalizes_character_notes():
    state = BuilderState(
        class_name="Wizard",
        level=5,
        look_ahead=False,
        ability_scores=ABILITY_SCORES,
        skill_proficiencies=SKILL_PROFICIENCIES,
        character_notes="  Track spell slots.\n\n  Buy ink.  \n",
    )

    payload = serialize_builder_state(state)
    restored = deserialize_builder_state(payload, available_classes=CLASSES)

    assert payload["builder"]["character_notes"] == "Track spell slots.\nBuy ink."
    assert restored.character_notes == "Track spell slots.\nBuy ink."


def test_serialize_builder_state_includes_combined_cross_section_fields():
    state = BuilderState(
        class_name="Wizard",
        level=3,
        look_ahead=True,
        ability_scores={"DEX": 18, "STR": 9, "CON": 14, "INT": 16, "WIS": 11, "CHA": 12},
        skill_proficiencies={"Athletics": 1, "Perception": "", "Arcana": "yes", "Acrobatics": 0},
        languages=" Common, Elvish, Common ",
        starting_gold="42",
        inventory_text="  Rope\n\n Torch  ",
    )

    payload = serialize_builder_state(state)
    builder_payload = payload["builder"]

    assert set(builder_payload.keys()) >= {
        "ability_scores",
        "skill_proficiencies",
        "languages",
        "starting_gold",
        "inventory_text",
    }
    assert builder_payload["ability_scores"] == {
        "STR": 9,
        "DEX": 18,
        "CON": 14,
        "INT": 16,
        "WIS": 11,
        "CHA": 12,
    }
    assert builder_payload["skill_proficiencies"] == {
        "Acrobatics": False,
        "Arcana": True,
        "Athletics": True,
        "Perception": False,
    }
    assert builder_payload["languages"] == "Common, Elvish"
    assert builder_payload["starting_gold"] == 42
    assert builder_payload["inventory_text"] == "Rope\nTorch"


def test_app_state_deserialize_serialize_canonicalizes_combined_payload_deterministically():
    payload = {
        "shell": {
            "title_text": "  ",
            "status_text": "",
            "active_tab": "Not A Tab",
        },
        "builder": {
            "class_name": "Unknown",
            "level": "99",
            "look_ahead": "1",
            "ability_scores": {"WIS": "11", "STR": "31", "CON": -5, "DEX": " 14 ", "CHA": None},
            "skill_proficiencies": {"Athletics": "on", "Arcana": "", "Perception": 2},
            "languages": " Common, , Dwarvish, Common ",
            "starting_gold": "-100",
            "inventory_text": "  Bedroll\n\n Rope  ",
        },
    }

    restored = deserialize_app_state(
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    canonical_once = serialize_app_state(restored)
    canonical_twice = serialize_app_state(
        deserialize_app_state(
            canonical_once,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
        )
    )

    assert canonical_once == {
        "builder": {
            "class_name": "Cleric",
            "level": 20,
            "look_ahead": True,
            "ability_scores": {
                "STR": 30,
                "DEX": 14,
                "CON": 1,
                "INT": 10,
                "WIS": 11,
                "CHA": 10,
            },
            "skill_proficiencies": {
                "Acrobatics": False,
                "Arcana": False,
                "Athletics": True,
                "Perception": True,
            },
            "character_name": "",
            "race_species": "",
            "background": "",
            "trait": "",
            "ideal": "",
            "bond": "",
            "flaw": "",
            "alignment": "",
            "character_notes": "",
            "languages": "Common, Dwarvish",
            "starting_gold": 0,
            "inventory_text": "Bedroll\nRope",
            "prepared_spells_text": "",
        },
        "shell": {
            "title_text": "D&D Character Creator V3",
            "status_text": "Ready",
            "active_tab": "Builder",
        },
    }
    assert canonical_twice == canonical_once


def test_state_payload_file_round_trip_preserves_serialized_app_state(tmp_path: Path):
    state = AppState(
        shell=AppShellState(
            title_text="Campaign: Tomb of Annihilation",
            status_text="Checkpoint",
            active_tab="Builder",
        ),
        builder=BuilderState(
            class_name="Wizard",
            level=6,
            look_ahead=True,
            ability_scores=ABILITY_SCORES,
            skill_proficiencies=SKILL_PROFICIENCIES,
            languages="Common, Elvish",
            starting_gold=40,
            inventory_text="Spellbook\nInk",
            prepared_spells_text="Mage Armor\nShield",
        ),
    )

    payload = serialize_app_state(state)
    target = write_state_payload(tmp_path / "outputs" / "v3_last_state.json", payload)
    loaded_payload = read_state_payload(target)
    restored = deserialize_app_state(
        loaded_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert loaded_payload == payload
    assert restored == state


def test_read_state_payload_rejects_non_object_json(tmp_path: Path):
    target = tmp_path / "bad_state.json"
    target.write_text("[]\n", encoding="utf-8")

    try:
        read_state_payload(target)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert str(exc) == "State file payload must be a JSON object"


def test_deserialize_builder_state_treats_non_object_builder_payload_as_empty():
    restored = deserialize_builder_state({"builder": ["not", "an", "object"]}, available_classes=CLASSES)

    assert restored == BuilderState(
        class_name="Cleric",
        level=1,
        look_ahead=False,
        ability_scores={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
        skill_proficiencies={
            "Acrobatics": False,
            "Arcana": False,
            "Athletics": False,
            "Perception": False,
        },
        languages="",
        starting_gold=0,
        inventory_text="",
        prepared_spells_text="",
    )


def test_deserialize_app_state_treats_non_object_shell_and_builder_payloads_as_empty_defaults():
    restored = deserialize_app_state(
        {"shell": "bad", "builder": 123},
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert restored == AppState(
        shell=AppShellState(
            title_text="D&D Character Creator V3",
            status_text="Ready",
            active_tab="Builder",
        ),
        builder=BuilderState(
            class_name="Cleric",
            level=1,
            look_ahead=False,
            ability_scores={"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
            skill_proficiencies={
                "Acrobatics": False,
                "Arcana": False,
                "Athletics": False,
                "Perception": False,
            },
            languages="",
            starting_gold=0,
            inventory_text="",
            prepared_spells_text="",
        ),
    )


def test_write_and_read_state_payload_produce_stable_canonical_json_text(tmp_path: Path):
    payload = {
        "shell": {"status_text": "Saved", "title_text": "T", "active_tab": "Builder"},
        "builder": {"level": 2, "class_name": "Wizard", "look_ahead": True},
    }

    target = write_state_payload(tmp_path / "state.json", payload)
    text = target.read_text(encoding="utf-8")

    assert text.endswith("\n")
    assert text == (
        "{\n"
        "  \"builder\": {\n"
        "    \"class_name\": \"Wizard\",\n"
        "    \"level\": 2,\n"
        "    \"look_ahead\": true\n"
        "  },\n"
        "  \"shell\": {\n"
        "    \"active_tab\": \"Builder\",\n"
        "    \"status_text\": \"Saved\",\n"
        "    \"title_text\": \"T\"\n"
        "  }\n"
        "}\n"
    )
    assert read_state_payload(target) == payload


def test_builder_payload_json_helpers_round_trip_canonical_and_deterministic():
    mixed_payload = {
        "builder": {
            "class_name": "Wizard",
            "level": "99",
            "look_ahead": 1,
            "ability_scores": {"STR": "31", "DEX": -5, "INT": "16"},
            "skill_proficiencies": {"Arcana": "yes", "Perception": ""},
            "languages": " Common, Elvish, Common ",
            "starting_gold": "45",
            "inventory_text": " Rope\n\n Torch ",
            "prepared_spells_text": "Mage Armor\n\nShield\nMage Armor",
        }
    }

    exported_once = export_builder_payload_json(mixed_payload, available_classes=CLASSES)
    imported_payload = import_builder_payload_json(exported_once, available_classes=CLASSES)
    exported_twice = export_builder_payload_json(imported_payload, available_classes=CLASSES)

    assert exported_twice == exported_once
    assert imported_payload == serialize_builder_state(
        deserialize_builder_state(mixed_payload, available_classes=CLASSES)
    )


def test_app_payload_json_helpers_round_trip_canonical_and_deterministic():
    mixed_payload = {
        "shell": {"title_text": "  ", "status_text": "", "active_tab": "Nope"},
        "builder": {
            "class_name": "Unknown",
            "level": 0,
            "look_ahead": True,
            "ability_scores": {"STR": 18, "DEX": 14},
        },
    }

    exported_once = export_app_payload_json(
        mixed_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    imported_payload = import_app_payload_json(
        exported_once,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    exported_twice = export_app_payload_json(
        imported_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert exported_twice == exported_once
    assert imported_payload == serialize_app_state(
        deserialize_app_state(
            mixed_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
        )
    )


def test_builder_payload_json_helpers_round_trip_unicode_and_special_content():
    payload = {
        "builder": {
            "class_name": "Wizard",
            "level": 7,
            "look_ahead": False,
            "character_name": "  Éowyn 🛡️ \"The Brave\"  ",
            "race_species": "  半精灵 / Half-Elf  ",
            "background": "  Sage\\Scholar — Δ  ",
            "alignment": "Neutral Good",
            "languages": " Common, Draconic, 日本語, Common, لغة\u200f ",
            "inventory_text": "  Rope (50ft)\n\nPotion: Healing ×2\n徽章\nLine with \\\"quotes\\\" & backslash \\\\\\ ",
            "prepared_spells_text": "  Mage Armor\n\nShield\nMisty Step✨\nShield\n", 
        }
    }

    exported = export_builder_payload_json(payload, available_classes=CLASSES)
    imported = import_builder_payload_json(exported, available_classes=CLASSES)

    assert imported == serialize_builder_state(
        deserialize_builder_state(payload, available_classes=CLASSES)
    )
    assert "Misty Step✨" in imported["builder"]["prepared_spells_text"]


def test_json_payload_helpers_are_deterministic_for_large_multiline_text():
    inventory_lines = [f"  Item {index:03d} — 測試 ✨  " for index in range(1, 151)]
    spells_lines = [f"  Spell {index:03d}  " for index in range(1, 101)] + [
        "  Spell 050  ",
        "",
        "  Spell 001  ",
    ]

    payload = {
        "shell": {"title_text": "Bulk Save", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {
            "class_name": "Wizard",
            "level": 10,
            "look_ahead": True,
            "character_name": "Archivist",
            "race_species": "Human",
            "background": "Sage",
            "alignment": "Lawful Neutral",
            "languages": "Common, Draconic, Elvish",
            "inventory_text": "\n".join(inventory_lines),
            "prepared_spells_text": "\n".join(spells_lines),
        },
    }

    exported_once = export_app_payload_json(
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    imported = import_app_payload_json(
        exported_once,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    exported_twice = export_app_payload_json(
        imported,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert exported_twice == exported_once
    assert imported == serialize_app_state(
        deserialize_app_state(
            payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
        )
    )


def test_import_payload_json_helpers_reject_invalid_json_and_non_object_payloads():
    for importer in (
        lambda text: import_builder_payload_json(text, available_classes=CLASSES),
        lambda text: import_app_payload_json(
            text,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
        ),
    ):
        try:
            importer("not-json")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert str(exc).startswith("Invalid JSON:")

        try:
            importer("[]")
            assert False, "Expected ValueError"
        except ValueError as exc:
            assert str(exc) == "Imported payload must be a JSON object"


def test_default_state_path_matches_save_load_contract_location():
    assert DEFAULT_STATE_PATH == Path("outputs") / "v3_last_state.json"
