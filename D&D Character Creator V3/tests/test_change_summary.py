from cc_v3.app import generate_export_summary_with_checkpoint_fallback
from cc_v3.persistence import (
    export_app_payload_json,
    import_app_payload_json,
    pop_undo_checkpoint,
    push_app_undo_checkpoint,
    read_state_payload,
    summarize_app_payload_changes,
    write_state_payload,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]


def _base_payload() -> dict:
    return {
        "shell": {
            "title_text": "D&D Character Creator V3",
            "status_text": "Ready",
            "active_tab": "Builder",
        },
        "builder": {
            "class_name": "Wizard",
            "level": 3,
            "look_ahead": False,
            "ability_scores": {"STR": 8, "DEX": 14, "CON": 12, "INT": 16, "WIS": 10, "CHA": 10},
            "skill_proficiencies": {
                "Acrobatics": False,
                "Arcana": True,
                "Athletics": False,
                "Perception": True,
            },
            "character_name": "Elora",
            "race_species": "Elf",
            "background": "Sage",
            "alignment": "Neutral Good",
            "languages": "Common, Elvish",
            "starting_gold": 20,
            "inventory_text": "Spellbook\nWand",
            "prepared_spells_text": "Mage Armor\nShield",
        },
    }


def test_change_summary_no_change_returns_empty_list():
    payload = _base_payload()

    changes = summarize_app_payload_changes(
        payload,
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes == []


def test_change_summary_single_field_change_reports_one_line():
    before = _base_payload()
    after = _base_payload()
    after["builder"]["level"] = 4

    changes = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes == ["Class/Level: Wizard 3 (look-ahead=off) -> Wizard 4 (look-ahead=off)"]


def test_change_summary_multi_field_is_deterministic_and_human_readable():
    before = _base_payload()
    after = {
        "builder": {
            "prepared_spells_text": "Shield\nMagic Missile",
            "inventory_text": "Wand\nRations",
            "starting_gold": 25,
            "alignment": "Chaotic Good",
            "background": "Soldier",
            "race_species": "Human",
            "character_name": "Mira",
            "skill_proficiencies": {
                "Perception": False,
                "Athletics": True,
                "Arcana": True,
                "Acrobatics": False,
            },
            "ability_scores": {"CHA": 12, "WIS": 10, "INT": 17, "CON": 12, "DEX": 14, "STR": 8},
            "look_ahead": True,
            "level": 4,
            "class_name": "Fighter",
            "languages": "Common, Dwarvish",
        },
        "shell": {
            "active_tab": "Library",
            "status_text": "Loaded",
            "title_text": "D&D Character Creator V3",
        },
    }

    expected = [
        "Identity: Elora | Elf | Sage | Neutral Good -> Mira | Human | Soldier | Chaotic Good",
        "Class/Level: Wizard 3 (look-ahead=off) -> Fighter 4 (look-ahead=on)",
        "Ability Scores: INT 16→17; CHA 10→12",
        "Skills: Arcana, Perception -> Arcana, Athletics",
        "Languages: removed [Elvish]; added [Dwarvish]",
        "Equipment: removed [Spellbook]; added [Rations]",
        "Spells: removed [Mage Armor]; added [Magic Missile]",
        "Gold: 20 -> 25",
        "Status: Ready -> Loaded",
        "Active Tab: Builder -> Library",
    ]

    changes = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    changes_repeat = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes == expected
    assert changes_repeat == expected


def test_change_summary_checkpoint_save_load_sequence_reports_deterministic_lines(tmp_path):
    previous_payload, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            _base_payload(),
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )
    )

    current_mutated = _base_payload()
    current_mutated["builder"]["level"] = 4
    current_mutated["builder"]["languages"] = "Common, Elvish, Draconic"
    current_mutated["builder"]["inventory_text"] = "Spellbook\nWand\nRations"
    current_mutated["builder"]["starting_gold"] = 30
    current_mutated["shell"]["status_text"] = "Loaded"
    current_mutated["shell"]["active_tab"] = "Library"

    target = write_state_payload(tmp_path / "state.json", current_mutated)
    loaded_current = read_state_payload(target)
    current_payload, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            loaded_current,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )
    )

    expected = [
        "Class/Level: Wizard 3 (look-ahead=off) -> Wizard 4 (look-ahead=off)",
        "Languages: added [Draconic]",
        "Equipment: added [Rations]",
        "Gold: 20 -> 30",
        "Status: Ready -> Loaded",
        "Active Tab: Builder -> Library",
    ]

    changes = summarize_app_payload_changes(
        previous_payload,
        current_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes == expected


def test_change_summary_no_change_after_canonical_round_trip_cycles(tmp_path):
    mixed_payload = {
        "shell": {"title_text": "", "status_text": "", "active_tab": "Nope"},
        "builder": {
            "class_name": "Unknown",
            "level": "99",
            "look_ahead": "",
            "ability_scores": {"STR": "31", "DEX": -5, "INT": "16"},
            "skill_proficiencies": {"Arcana": "yes", "Perception": ""},
            "languages": " Common, Elvish, Common ",
            "starting_gold": "45",
            "inventory_text": " Rope\n\n Torch ",
            "prepared_spells_text": "Mage Armor\n\nShield\nMage Armor",
        },
    }

    canonical_once, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            mixed_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )
    )

    target = write_state_payload(tmp_path / "round-trip.json", canonical_once)
    reloaded = read_state_payload(target)
    canonical_twice, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            reloaded,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )
    )

    assert summarize_app_payload_changes(
        canonical_once,
        canonical_twice,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    ) == []


def test_change_summary_compatible_with_export_summary_checkpoint_fallback_selection():
    restored_checkpoint_payload = _base_payload()
    current_payload = _base_payload()
    current_payload["builder"]["character_name"] = "Mira"
    current_payload["builder"]["level"] = 4

    restored_summary = generate_export_summary_with_checkpoint_fallback(
        current_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
        prefer_restored_checkpoint=True,
        restored_checkpoint_payload=restored_checkpoint_payload,
    )
    current_summary = generate_export_summary_with_checkpoint_fallback(
        current_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
        prefer_restored_checkpoint=False,
        restored_checkpoint_payload=restored_checkpoint_payload,
    )

    assert "Identity: Elora | Elf | Sage | Neutral Good" in restored_summary
    assert "Identity: Mira | Elf | Sage | Neutral Good" in current_summary

    assert summarize_app_payload_changes(
        restored_checkpoint_payload,
        current_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    ) == [
        "Identity: Elora | Elf | Sage | Neutral Good -> Mira | Elf | Sage | Neutral Good",
        "Class/Level: Wizard 3 (look-ahead=off) -> Wizard 4 (look-ahead=off)",
    ]


def _cycle_app_payload(payload: dict, *, cycles: int) -> dict:
    current = payload
    for _ in range(cycles):
        exported = export_app_payload_json(
            current,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
        )
        current = import_app_payload_json(
            exported,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
        )
    return current


def test_change_summary_no_drift_after_repeated_json_export_import_cycles():
    mixed_payload = {
        "shell": {"title_text": "", "status_text": "", "active_tab": "Nope"},
        "builder": {
            "class_name": "Unknown",
            "level": "99",
            "look_ahead": "",
            "ability_scores": {"STR": "31", "DEX": -5, "INT": "16"},
            "skill_proficiencies": {"Arcana": "yes", "Perception": ""},
            "languages": " Common, Elvish, Common ",
            "starting_gold": "45",
            "inventory_text": " Rope\n\n Torch ",
            "prepared_spells_text": "Mage Armor\n\nShield\nMage Armor",
        },
    }

    canonical_once = _cycle_app_payload(mixed_payload, cycles=1)
    canonical_after_many = _cycle_app_payload(mixed_payload, cycles=6)

    assert summarize_app_payload_changes(
        canonical_once,
        canonical_after_many,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    ) == []


def test_change_summary_stable_order_with_meaningful_deltas_after_repeated_cycles():
    before = _cycle_app_payload(_base_payload(), cycles=4)
    after_raw = _base_payload()
    after_raw["builder"].update(
        {
            "character_name": "Mira",
            "race_species": "Human",
            "background": "Soldier",
            "alignment": "Chaotic Good",
            "class_name": "Fighter",
            "level": 4,
            "look_ahead": True,
            "ability_scores": {"CHA": 12, "WIS": 10, "INT": 17, "CON": 12, "DEX": 14, "STR": 8},
            "skill_proficiencies": {
                "Perception": False,
                "Athletics": True,
                "Arcana": True,
                "Acrobatics": False,
            },
            "languages": "Common, Dwarvish",
            "inventory_text": "Wand\nRations",
            "prepared_spells_text": "Shield\nMagic Missile",
            "starting_gold": 25,
        }
    )
    after_raw["shell"]["status_text"] = "Loaded"
    after_raw["shell"]["active_tab"] = "Library"
    after = _cycle_app_payload(after_raw, cycles=5)

    expected = [
        "Identity: Elora | Elf | Sage | Neutral Good -> Mira | Human | Soldier | Chaotic Good",
        "Class/Level: Wizard 3 (look-ahead=off) -> Fighter 4 (look-ahead=on)",
        "Ability Scores: INT 16→17; CHA 10→12",
        "Skills: Arcana, Perception -> Arcana, Athletics",
        "Languages: removed [Elvish]; added [Dwarvish]",
        "Equipment: removed [Spellbook]; added [Rations]",
        "Spells: removed [Mage Armor]; added [Magic Missile]",
        "Gold: 20 -> 25",
        "Status: Ready -> Loaded",
        "Active Tab: Builder -> Library",
    ]

    changes = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    changes_repeat = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes == expected
    assert changes_repeat == expected


def test_change_summary_reports_order_only_deltas_for_languages_equipment_and_spells():
    before = _base_payload()
    after = _base_payload()
    after["builder"]["languages"] = "Elvish, Common"
    after["builder"]["inventory_text"] = "Wand\nSpellbook"
    after["builder"]["prepared_spells_text"] = "Shield\nMage Armor"

    changes = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes == [
        "Languages: Common, Elvish -> Elvish, Common",
        "Equipment order changed: 2 items -> 2 items",
        "Spells order changed: 2 entries -> 2 entries",
    ]


def test_change_summary_sorts_added_removed_items_deterministically_with_multi_item_deltas():
    before = _base_payload()
    after = _base_payload()
    after["builder"]["languages"] = "Common, Draconic, Aarakocra"
    after["builder"]["inventory_text"] = "Wand\nRope\nArrow"
    after["builder"]["prepared_spells_text"] = "Shield\nAbsorb Elements\nFireball"

    changes = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes == [
        "Languages: removed [Elvish]; added [Aarakocra, Draconic]",
        "Equipment: removed [Spellbook]; added [Arrow, Rope]",
        "Spells: removed [Mage Armor]; added [Absorb Elements, Fireball]",
    ]


def test_change_summary_includes_character_notes_delta_in_deterministic_personality_order():
    before = _cycle_app_payload(_base_payload(), cycles=2)
    after_raw = _base_payload()
    after_raw["builder"].update(
        {
            "trait": "  I annotate every map margin.  ",
            "ideal": " Knowledge belongs to everyone. ",
            "bond": "  The old academy archive\n",
            "flaw": "  I over-plan everything. ",
            "character_notes": "  Keep route plans in one notebook.\n\n  Buy more ink.  ",
        }
    )

    after = _cycle_app_payload(after_raw, cycles=5)

    expected = [
        "Trait: None -> I annotate every map margin.",
        "Ideal: None -> Knowledge belongs to everyone.",
        "Bond: None -> The old academy archive",
        "Flaw: None -> I over-plan everything.",
        "Character Notes: None -> Keep route plans in one notebook.\nBuy more ink.",
    ]

    changes_once = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    changes_twice = summarize_app_payload_changes(
        before,
        _cycle_app_payload(after, cycles=3),
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes_once == expected
    assert changes_twice == expected


def test_change_summary_personality_line_order_stable_across_canonical_cycles():
    before = _cycle_app_payload(_base_payload(), cycles=2)
    after_raw = _base_payload()
    after_raw["builder"].update(
        {
            "trait": "  I annotate every map margin.  ",
            "ideal": " Knowledge belongs to everyone. ",
            "bond": "  The old academy archive\n",
            "flaw": "  I over-plan everything. ",
            "character_notes": "  Keep ink dry.  ",
        }
    )

    after = _cycle_app_payload(after_raw, cycles=5)

    expected = [
        "Trait: None -> I annotate every map margin.",
        "Ideal: None -> Knowledge belongs to everyone.",
        "Bond: None -> The old academy archive",
        "Flaw: None -> I over-plan everything.",
        "Character Notes: None -> Keep ink dry.",
    ]

    changes_once = summarize_app_payload_changes(
        before,
        after,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    changes_twice = summarize_app_payload_changes(
        before,
        _cycle_app_payload(after, cycles=3),
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert changes_once == expected
    assert changes_twice == expected
