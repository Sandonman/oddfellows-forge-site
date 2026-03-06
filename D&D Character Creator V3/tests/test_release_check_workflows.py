from cc_v3.app import generate_export_summary_with_checkpoint_fallback
from cc_v3.persistence import (
    export_app_payload_json,
    import_app_payload_json,
    pop_undo_checkpoint,
    push_app_undo_checkpoint,
    summarize_app_payload_changes,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]
TABS = ("Builder", "Library")


def _payload(
    *,
    level: int,
    languages: str,
    trait: str = "",
    ideal: str = "",
    bond: str = "",
    flaw: str = "",
) -> dict:
    return {
        "shell": {
            "title_text": "D&D Character Creator V3",
            "status_text": "Ready",
            "active_tab": "Builder",
        },
        "builder": {
            "class_name": "Wizard",
            "level": level,
            "look_ahead": False,
            "ability_scores": {"STR": 8, "DEX": 14, "CON": 12, "INT": 16, "WIS": 10, "CHA": 10},
            "skill_proficiencies": {
                "Acrobatics": False,
                "Arcana": True,
                "Athletics": False,
                "Perception": True,
            },
            "character_name": "  Elora ",
            "race_species": " Elf ",
            "background": " Sage ",
            "alignment": "Neutral Good",
            "trait": trait,
            "ideal": ideal,
            "bond": bond,
            "flaw": flaw,
            "languages": languages,
            "starting_gold": 20,
            "inventory_text": "Spellbook\nWand",
            "prepared_spells_text": "Mage Armor\nShield",
        },
    }


def test_release_check_helper_workflow_chain_stays_green_together():
    normalized_previous = import_app_payload_json(
        export_app_payload_json(_payload(level=3, languages="Common, Elvish"), available_classes=CLASSES),
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    restored_checkpoint, remaining = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            normalized_previous,
            available_classes=CLASSES,
            available_tabs=TABS,
            capacity=5,
        )
    )
    assert remaining == ()

    normalized_current = import_app_payload_json(
        export_app_payload_json(_payload(level=4, languages="Common, Elvish, Draconic"), available_classes=CLASSES),
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    fallback_summary = generate_export_summary_with_checkpoint_fallback(
        normalized_current,
        available_classes=CLASSES,
        available_tabs=TABS,
        prefer_restored_checkpoint=True,
        restored_checkpoint_payload=restored_checkpoint,
    )

    assert "Identity: Elora | Elf | Sage | Neutral Good" in fallback_summary
    assert "Class/Level: Wizard 3" in fallback_summary
    assert "Class/Level: Wizard 4" not in fallback_summary

    assert summarize_app_payload_changes(
        restored_checkpoint,
        normalized_current,
        available_classes=CLASSES,
        available_tabs=TABS,
    ) == [
        "Class/Level: Wizard 3 (look-ahead=off) -> Wizard 4 (look-ahead=off)",
        "Languages: added [Draconic]",
    ]


def test_release_check_checkpoint_fallback_keeps_personality_fields_through_push_pop():
    normalized_previous = import_app_payload_json(
        export_app_payload_json(
            _payload(
                level=3,
                languages="Common, Elvish",
                trait="  Curious about ancient wards.  ",
                ideal=" Knowledge should be shared. ",
                bond=" The old academy archive ",
                flaw=" I underestimate practical people. ",
            ),
            available_classes=CLASSES,
        ),
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    restored_checkpoint, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            normalized_previous,
            available_classes=CLASSES,
            available_tabs=TABS,
            capacity=5,
        )
    )

    normalized_current = import_app_payload_json(
        export_app_payload_json(
            _payload(
                level=4,
                languages="Common, Elvish, Draconic",
                trait="I leave chalk marks everywhere.",
                ideal="Power is safety.",
                bond="My old tower.",
                flaw="I hoard secrets.",
            ),
            available_classes=CLASSES,
        ),
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    fallback_summary = generate_export_summary_with_checkpoint_fallback(
        normalized_current,
        available_classes=CLASSES,
        available_tabs=TABS,
        prefer_restored_checkpoint=True,
        restored_checkpoint_payload=restored_checkpoint,
    )

    assert "Class/Level: Wizard 3" in fallback_summary
    assert "Personality: Trait=Curious about ancient wards." in fallback_summary
    assert "Ideal=Knowledge should be shared." in fallback_summary
    assert "Bond=The old academy archive" in fallback_summary
    assert "Flaw=I underestimate practical people." in fallback_summary
    assert "I leave chalk marks everywhere." not in fallback_summary


def test_release_check_checkpoint_fallback_keeps_derived_combat_stable_across_canonicalization_cycles():
    restored_checkpoint, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            _payload(level=3, languages="Common, Elvish"),
            available_classes=CLASSES,
            available_tabs=TABS,
            capacity=5,
        )
    )

    current_payload = _payload(level=4, languages="Common, Elvish, Draconic")
    expected_derived_line = (
        "Derived Combat: Initiative +2 | Passive Perception 12 | "
        "Attack Baseline +4 to hit, +2 damage mod (best STR/DEX)"
    )

    for _ in range(6):
        restored_checkpoint = import_app_payload_json(
            export_app_payload_json(restored_checkpoint, available_classes=CLASSES, available_tabs=TABS),
            available_classes=CLASSES,
            available_tabs=TABS,
        )
        current_payload = import_app_payload_json(
            export_app_payload_json(current_payload, available_classes=CLASSES, available_tabs=TABS),
            available_classes=CLASSES,
            available_tabs=TABS,
        )

        fallback_summary = generate_export_summary_with_checkpoint_fallback(
            current_payload,
            available_classes=CLASSES,
            available_tabs=TABS,
            prefer_restored_checkpoint=True,
            restored_checkpoint_payload=restored_checkpoint,
        )

        assert expected_derived_line in fallback_summary
        assert "Class/Level: Wizard 3" in fallback_summary
        assert "Class/Level: Wizard 4" not in fallback_summary
