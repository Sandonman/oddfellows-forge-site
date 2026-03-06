import cc_v3
from cc_v3 import create_main_window, run_app
from cc_v3.app import DEFAULT_WINDOW_TITLE, generate_export_summary_from_payload


def test_app_shell_exports_and_default_title():
    assert callable(create_main_window)
    assert callable(run_app)
    assert DEFAULT_WINDOW_TITLE == "D&D Character Creator V3"


def test_public_export_surface_contract_is_stable():
    expected_exports = {
        "CharacterCreatorApp",
        "create_main_window",
        "run_app",
        "BuilderTab",
        "attach_builder_tab",
        "format_builder_summary",
        "LibraryTab",
        "attach_library_tab",
        "format_library_detail",
        "load_library_index",
        "format_character_export_summary",
        "MAX_LEVEL",
        "LevelSnapshot",
        "load_classes",
        "build_level_snapshot",
        "level_up",
        "BuilderState",
        "AppShellState",
        "AppState",
        "serialize_builder_state",
        "deserialize_builder_state",
        "serialize_app_state",
        "deserialize_app_state",
        "export_builder_payload_json",
        "import_builder_payload_json",
        "export_app_payload_json",
        "import_app_payload_json",
        "summarize_app_payload_changes",
        "summarize_release_candidate_readiness",
    }

    assert set(cc_v3.__all__) == expected_exports
    assert len(cc_v3.__all__) == len(expected_exports)
    for name in cc_v3.__all__:
        assert hasattr(cc_v3, name)



def test_generate_export_summary_from_payload_uses_current_normalized_state():
    payload = {
        "shell": {
            "title_text": "Campaign",
            "status_text": "Ready",
            "active_tab": "Builder",
        },
        "builder": {
            "class_name": "Wizard",
            "level": "5",
            "look_ahead": 1,
            "ability_scores": {
                "STR": "8",
                "DEX": "14",
                "CON": "13",
                "INT": "18",
                "WIS": "12",
                "CHA": "10",
            },
            "skill_proficiencies": {
                "Acrobatics": 0,
                "Arcana": 1,
                "Athletics": "",
                "Perception": True,
            },
            "character_name": "  Elora  ",
            "race_species": " Elf ",
            "background": " Sage  ",
            "alignment": "Neutral Good",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "24",
            "inventory_text": " Spellbook\n\nWand\nRations ",
            "prepared_spells_text": " Mage Armor\nMagic Missile\nShield\nMage Armor ",
        },
    }

    summary = generate_export_summary_from_payload(
        payload,
        available_classes=("Cleric", "Fighter", "Wizard"),
        available_tabs=("Builder", "Library"),
    )

    assert "Identity: Elora | Elf | Sage | Neutral Good" in summary
    assert "Class/Level: Wizard 5" in summary
    assert "Core Proficiencies: Arcana, Perception (2/4)" in summary
    assert "Languages: Common, Elvish" in summary
    assert "Equipment: 24 gp; 3 item(s): Spellbook, Wand, Rations" in summary
    assert "Spell Highlights: Mage Armor, Magic Missile, Shield" in summary
