from cc_v3.builder_tab import format_builder_summary, format_character_snapshot
from cc_v3.export_summary import format_character_export_summary
from cc_v3.leveling import build_level_snapshot
from cc_v3.persistence import (
    AppShellState,
    AppState,
    BuilderState,
    deserialize_app_state,
    export_app_payload_json,
    import_app_payload_json,
    serialize_app_state,
)


def _line_value(text: str, prefix: str) -> str:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    raise AssertionError(f"Missing line with prefix: {prefix!r}")


def _format_all(state: AppState) -> tuple[str, str, str]:
    builder = state.builder
    snap = build_level_snapshot(builder.class_name, builder.level, look_ahead=builder.look_ahead)

    builder_summary = format_builder_summary(
        snap,
        look_ahead=builder.look_ahead,
        character_name=builder.character_name,
        race_species=builder.race_species,
        background=builder.background,
        trait=builder.trait,
        ideal=builder.ideal,
        bond=builder.bond,
        flaw=builder.flaw,
        character_notes=builder.character_notes,
        alignment=builder.alignment,
        ability_scores=builder.ability_scores,
        skill_proficiencies=builder.skill_proficiencies,
        languages=builder.languages,
        starting_gold=builder.starting_gold,
        inventory_text=builder.inventory_text,
        prepared_spells_text=builder.prepared_spells_text,
    )
    snapshot = format_character_snapshot(
        snap,
        character_name=builder.character_name,
        race_species=builder.race_species,
        background=builder.background,
        trait=builder.trait,
        ideal=builder.ideal,
        bond=builder.bond,
        flaw=builder.flaw,
        character_notes=builder.character_notes,
        alignment=builder.alignment,
        ability_scores=builder.ability_scores,
        skill_proficiencies=builder.skill_proficiencies,
        languages=builder.languages,
        starting_gold=builder.starting_gold,
        inventory_text=builder.inventory_text,
        prepared_spells_text=builder.prepared_spells_text,
    )
    export = format_character_export_summary(state)

    return builder_summary, snapshot, export


def test_summary_snapshot_export_share_normalized_key_values():
    state = AppState(
        shell=AppShellState(title_text="Campaign", status_text="Ready", active_tab="Builder"),
        builder=BuilderState(
            class_name="Wizard",
            level=5,
            look_ahead=True,
            ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 18, "WIS": 12, "CHA": 10},
            skill_proficiencies={"Acrobatics": False, "Arcana": True, "Athletics": False, "Perception": True},
            character_name="Elora",
            race_species="Elf",
            background="Sage",
            alignment="Neutral Good",
            languages="Common, Elvish",
            starting_gold=24,
            inventory_text="Spellbook\nWand\nRations",
            prepared_spells_text="Mage Armor\nMagic Missile\nShield",
        ),
    )

    builder_summary, snapshot, export = _format_all(state)

    assert _line_value(builder_summary, "Validation: ") == "OK"
    assert _line_value(export, "Validation Status: ") == "OK"

    shared_snapshot_fields = ["Identity: ", "Personality: ", "Class/Level: ", "Ability Scores: ", "Derived Combat: ", "Languages: "]
    for prefix in shared_snapshot_fields:
        assert _line_value(builder_summary, prefix) == _line_value(snapshot, prefix)

    assert _line_value(snapshot, "Identity: ") == _line_value(export, "Identity: ")
    assert _line_value(snapshot, "Class/Level: ") == _line_value(export, "Class/Level: ")
    assert _line_value(snapshot, "Ability Scores: ") == _line_value(export, "Ability Scores: ")
    assert _line_value(snapshot, "Derived Combat: ") == _line_value(export, "Derived Combat: ")
    assert _line_value(snapshot, "Languages: ") == _line_value(export, "Languages: ")

    assert _line_value(snapshot, "Skills: ") == _line_value(export, "Core Proficiencies: ")
    assert _line_value(snapshot, "Equipment: ") == _line_value(export, "Equipment: ")


def test_summary_snapshot_export_stay_coherent_after_dirty_payload_persistence_normalization():
    payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {
            "class_name": "Wizard",
            "level": "5",
            "look_ahead": 1,
            "ability_scores": {"STR": "8", "DEX": "14", "CON": "13", "INT": "18", "WIS": "12", "CHA": "10"},
            "skill_proficiencies": {"Acrobatics": 0, "Arcana": "yes", "Athletics": "", "Perception": 1},
            "character_name": "  Elora  ",
            "race_species": " Elf ",
            "background": " Sage  ",
            "trait": "  Keeps notes.  \n",
            "ideal": "  Knowledge should be shared.  ",
            "bond": "  The old academy archive.  ",
            "flaw": "  Overthinks simple choices.  ",
            "alignment": "Neutral Good",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "24",
            "inventory_text": " Spellbook\n\nWand\nRations ",
            "prepared_spells_text": " Mage Armor\nMagic Missile\nShield\nMage Armor ",
        },
    }

    state = deserialize_app_state(payload, available_classes=["Cleric", "Fighter", "Wizard"], available_tabs=("Builder", "Library"))
    builder_summary, snapshot, export = _format_all(state)

    assert _line_value(builder_summary, "Validation: ") == "OK"
    assert _line_value(export, "Validation Status: ") == "OK"

    assert _line_value(builder_summary, "Identity: ") == _line_value(snapshot, "Identity: ")
    assert _line_value(snapshot, "Identity: ") == "Elora | Elf | Sage | Neutral Good"

    assert _line_value(builder_summary, "Class/Level: ") == _line_value(snapshot, "Class/Level: ")
    assert _line_value(snapshot, "Class/Level: ") == _line_value(export, "Class/Level: ")

    assert _line_value(builder_summary, "Ability Scores: ") == _line_value(snapshot, "Ability Scores: ")
    assert _line_value(snapshot, "Ability Scores: ") == _line_value(export, "Ability Scores: ")
    assert _line_value(builder_summary, "Derived Combat: ") == _line_value(snapshot, "Derived Combat: ")
    assert _line_value(snapshot, "Derived Combat: ") == _line_value(export, "Derived Combat: ")
    assert _line_value(builder_summary, "Personality: ") == _line_value(snapshot, "Personality: ")
    assert _line_value(snapshot, "Personality: ") == _line_value(export, "Personality: ")
    assert _line_value(snapshot, "Personality: ") == "Trait=Keeps notes. | Ideal=Knowledge should be shared. | Bond=The old academy archive. | Flaw=Overthinks simple choices."

    assert _line_value(builder_summary, "Skills: ") == "Arcana, Perception (2/4)"
    assert _line_value(snapshot, "Skills: ") == _line_value(export, "Core Proficiencies: ")
    assert _line_value(builder_summary, "Languages: ") == "Common, Elvish"
    assert _line_value(snapshot, "Languages: ") == _line_value(export, "Languages: ")
    assert _line_value(snapshot, "Equipment: ") == _line_value(export, "Equipment: ")


def test_notes_line_is_coherent_and_deterministic_across_summary_snapshot_export():
    payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {
            "class_name": "Wizard",
            "level": "5",
            "look_ahead": 1,
            "ability_scores": {"STR": "8", "DEX": "14", "CON": "13", "INT": "18", "WIS": "12", "CHA": "10"},
            "skill_proficiencies": {"Acrobatics": 0, "Arcana": "yes", "Athletics": "", "Perception": 1},
            "character_name": "  Elora  ",
            "race_species": " Elf ",
            "background": " Sage  ",
            "alignment": "Neutral Good",
            "character_notes": "  Keep rituals organized.\n\n  Buy ink and chalk weekly.\n  ",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "24",
            "inventory_text": " Spellbook\n\nWand\nRations ",
            "prepared_spells_text": " Mage Armor\nMagic Missile\nShield\nMage Armor ",
        },
    }

    state = deserialize_app_state(payload, available_classes=["Cleric", "Fighter", "Wizard"], available_tabs=("Builder", "Library"))

    builder_summary, snapshot, export = _format_all(state)

    expected_notes = "Keep rituals organized."
    assert _line_value(builder_summary, "- Character Notes: ") == expected_notes
    assert _line_value(snapshot, "Notes: ") == expected_notes
    assert _line_value(export, "Notes: ") == expected_notes

    canonical_payload = import_app_payload_json(
        export_app_payload_json(serialize_app_state(state), available_classes=["Cleric", "Fighter", "Wizard"], available_tabs=("Builder", "Library")),
        available_classes=["Cleric", "Fighter", "Wizard"],
        available_tabs=("Builder", "Library"),
    )
    cycled_state = deserialize_app_state(
        canonical_payload,
        available_classes=["Cleric", "Fighter", "Wizard"],
        available_tabs=("Builder", "Library"),
    )
    _, snapshot_after_cycle, export_after_cycle = _format_all(cycled_state)

    assert _line_value(snapshot_after_cycle, "Notes: ") == expected_notes
    assert _line_value(export_after_cycle, "Notes: ") == expected_notes


def test_notes_and_equipment_lines_apply_consistent_deterministic_truncation_across_snapshot_and_export():
    state = AppState(
        shell=AppShellState(title_text="Campaign", status_text="Ready", active_tab="Builder"),
        builder=BuilderState(
            class_name="Wizard",
            level=5,
            look_ahead=True,
            ability_scores={"STR": 8, "DEX": 14, "CON": 13, "INT": 18, "WIS": 12, "CHA": 10},
            skill_proficiencies={"Acrobatics": False, "Arcana": True, "Athletics": False, "Perception": True},
            character_name="Elora",
            race_species="Elf",
            background="Sage",
            alignment="Neutral Good",
            character_notes="Catalog every reagent and annotate every vial label before dawn patrol.",
            languages="Common, Elvish",
            starting_gold=24,
            inventory_text="Masterwork crystal focus with silver inlay\nRations\nRope\nTorch",
            prepared_spells_text="Mage Armor\nMagic Missile\nShield",
        ),
    )

    _, snapshot, export = _format_all(state)

    expected_notes = "Catalog every reagent and annotate every vial label before…"
    expected_equipment = "24 gp; 4 item(s): Masterwork crystal focu…, Rations, Rope, … (+1 more)"

    assert _line_value(snapshot, "Notes: ") == expected_notes
    assert _line_value(export, "Notes: ") == expected_notes
    assert _line_value(snapshot, "Equipment: ") == expected_equipment
    assert _line_value(export, "Equipment: ") == expected_equipment


def test_derived_combat_remains_deterministic_across_summary_snapshot_export_after_repeated_normalization_cycles():
    classes = ["Cleric", "Fighter", "Wizard"]
    tabs = ("Builder", "Library")
    payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {
            "class_name": "Wizard",
            "level": "5",
            "look_ahead": 1,
            "ability_scores": {"STR": "8", "DEX": "14", "CON": "13", "INT": "18", "WIS": "12", "CHA": "10"},
            "skill_proficiencies": {"Acrobatics": 0, "Arcana": "yes", "Athletics": "", "Perception": 1},
            "character_name": "  Elora  ",
            "race_species": " Elf ",
            "background": " Sage  ",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "24",
            "inventory_text": " Spellbook\n\nWand\nRations ",
            "prepared_spells_text": " Mage Armor\nMagic Missile\nShield\nMage Armor ",
        },
    }

    expected_line = "Initiative +2 | Passive Perception 14 | Attack Baseline +5 to hit, +2 damage mod (best STR/DEX)"

    for _ in range(6):
        state = deserialize_app_state(payload, available_classes=classes, available_tabs=tabs)
        builder_summary, snapshot, export = _format_all(state)

        builder_line = _line_value(builder_summary, "Derived Combat: ")
        snapshot_line = _line_value(snapshot, "Derived Combat: ")
        export_line = _line_value(export, "Derived Combat: ")

        assert builder_line == expected_line
        assert snapshot_line == expected_line
        assert export_line == expected_line

        payload = import_app_payload_json(
            export_app_payload_json(serialize_app_state(state), available_classes=classes, available_tabs=tabs),
            available_classes=classes,
            available_tabs=tabs,
        )
