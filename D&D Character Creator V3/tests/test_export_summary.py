from cc_v3.export_summary import format_character_export_summary
from cc_v3.persistence import AppShellState, AppState, BuilderState, deserialize_app_state


def test_format_character_export_summary_contains_required_sections():
    state = AppState(
        shell=AppShellState(
            title_text="D&D Character Creator V3",
            status_text="Ready",
            active_tab="Builder",
        ),
        builder=BuilderState(
            class_name="Wizard",
            level=5,
            look_ahead=False,
            ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 18, "WIS": 12, "CHA": 10},
            skill_proficiencies={
                "Acrobatics": False,
                "Arcana": True,
                "Athletics": False,
                "Perception": True,
            },
            character_name="Elora",
            race_species="Elf",
            background="Sage",
            alignment="Neutral Good",
            character_notes="Tracks rumors in the margins.",
            languages="Common, Elvish",
            starting_gold=24,
            inventory_text="Spellbook\nWand\nRations",
            prepared_spells_text="Mage Armor\nMagic Missile\nShield",
        ),
    )

    summary = format_character_export_summary(state)

    assert "Character Summary" in summary
    assert "Identity: Elora | Elf | Sage | Neutral Good" in summary
    assert "Class/Level: Wizard 5" in summary
    assert "Personality: Trait=None | Ideal=None | Bond=None | Flaw=None" in summary
    assert "Notes: Tracks rumors in the margins." in summary
    assert "Ability Scores: STR 8 (-1), DEX 14 (+2), CON 13 (+1), INT 18 (+4), WIS 12 (+1), CHA 10 (+0)" in summary
    assert "Derived Combat: Initiative +2 | Passive Perception 14 | Attack Baseline +5 to hit, +2 damage mod (best STR/DEX)" in summary
    assert "Core Proficiencies: Arcana, Perception (2/4)" in summary
    assert "Languages: Common, Elvish" in summary
    assert "Equipment: 24 gp; 3 item(s): Spellbook, Wand, Rations" in summary
    assert "Spell Highlights: Mage Armor, Magic Missile, Shield" in summary
    assert "Validation Status: OK" in summary


def test_format_character_export_summary_derived_combat_is_deterministic_and_normalized():
    classes = ["Cleric", "Fighter", "Wizard"]
    mixed_payload = {
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
        },
    }

    normalized_from_mixed = deserialize_app_state(
        mixed_payload,
        available_classes=classes,
        available_tabs=("Builder", "Library"),
    )

    summary = format_character_export_summary(normalized_from_mixed)
    assert "Derived Combat: Initiative +2 | Passive Perception 14 | Attack Baseline +5 to hit, +2 damage mod (best STR/DEX)" in summary


def test_format_character_export_summary_is_deterministic_for_mixed_vs_normalized_input():
    classes = ["Cleric", "Fighter", "Wizard"]
    mixed_payload = {
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
            "character_notes": "  Tracks rumors in the margins.\n\n  Check wards.  ",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "24",
            "inventory_text": " Spellbook\n\nWand\nRations ",
            "prepared_spells_text": " Mage Armor\nMagic Missile\nShield\nMage Armor ",
        },
    }

    normalized_from_mixed = deserialize_app_state(
        mixed_payload,
        available_classes=classes,
        available_tabs=("Builder", "Library"),
    )

    already_normalized = AppState(
        shell=AppShellState(
            title_text="Campaign",
            status_text="Ready",
            active_tab="Builder",
        ),
        builder=BuilderState(
            class_name="Wizard",
            level=5,
            look_ahead=True,
            ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 18, "WIS": 12, "CHA": 10},
            skill_proficiencies={
                "Acrobatics": False,
                "Arcana": True,
                "Athletics": False,
                "Perception": True,
            },
            character_name="Elora",
            race_species="Elf",
            background="Sage",
            alignment="Neutral Good",
            character_notes="Tracks rumors in the margins.\nCheck wards.",
            languages="Common, Elvish",
            starting_gold=24,
            inventory_text="Spellbook\nWand\nRations",
            prepared_spells_text="Mage Armor\nMagic Missile\nShield",
        ),
    )

    summary_from_mixed = format_character_export_summary(normalized_from_mixed)
    summary_from_normalized = format_character_export_summary(already_normalized)

    assert summary_from_mixed == summary_from_normalized
