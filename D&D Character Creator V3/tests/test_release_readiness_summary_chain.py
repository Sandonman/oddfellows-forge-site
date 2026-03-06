from cc_v3.app import generate_export_summary_from_payload
from cc_v3.persistence import (
    export_app_payload_json,
    import_app_payload_json,
    summarize_app_payload_changes,
    summarize_release_candidate_readiness,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]
TABS = ("Builder", "Library")


def _canonical_payload(payload: dict) -> dict:
    return import_app_payload_json(
        export_app_payload_json(payload, available_classes=CLASSES, available_tabs=TABS),
        available_classes=CLASSES,
        available_tabs=TABS,
    )


def _payload(*, identity: tuple[str, str, str, str], notes: str) -> dict:
    name, species, background, alignment = identity
    return {
        "shell": {
            "title_text": "D&D Character Creator V3",
            "status_text": "Ready",
            "active_tab": "Builder",
        },
        "builder": {
            "class_name": "Wizard",
            "level": 5,
            "look_ahead": False,
            "ability_scores": {"STR": 8, "DEX": 14, "CON": 12, "INT": 16, "WIS": 10, "CHA": 10},
            "skill_proficiencies": {
                "Acrobatics": False,
                "Arcana": True,
                "Athletics": False,
                "Perception": True,
            },
            "character_name": name,
            "race_species": species,
            "background": background,
            "alignment": alignment,
            "trait": "",
            "ideal": "",
            "bond": "",
            "flaw": "",
            "character_notes": notes,
            "languages": "Common, Elvish",
            "starting_gold": 24,
            "inventory_text": "Spellbook\nWand\nRations",
            "prepared_spells_text": "Mage Armor\nShield",
        },
    }


def test_readiness_summary_chain_ready_payload_matches_export_and_change_summaries():
    ready_payload = _canonical_payload(
        _payload(
            identity=("Elora", "Elf", "Sage", "Neutral Good"),
            notes="Tracks rumors",
        )
    )

    readiness = summarize_release_candidate_readiness(
        ready_payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )
    export_summary = generate_export_summary_from_payload(
        ready_payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )
    change_summary = summarize_app_payload_changes(
        ready_payload,
        ready_payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    assert readiness["ready"] is True
    assert [check["key"] for check in readiness["checks"]] == [
        "identity_complete",
        "class_level_valid",
        "ability_normalized",
        "notes_or_personality_present",
        "checkpoint_safe_payload_shape",
    ]
    assert [check["ok"] for check in readiness["checks"]] == [True, True, True, True, True]

    assert "Identity: Elora | Elf | Sage | Neutral Good" in export_summary
    assert "Class/Level: Wizard 5" in export_summary
    assert "Validation Status: OK" in export_summary
    assert change_summary == []


def test_readiness_summary_chain_not_ready_payload_matches_export_and_change_summaries():
    previous_ready_payload = _canonical_payload(
        _payload(
            identity=("Elora", "Elf", "Sage", "Neutral Good"),
            notes="Tracks rumors",
        )
    )
    not_ready_payload = _canonical_payload(
        _payload(
            identity=("", "", "", ""),
            notes="",
        )
    )

    readiness = summarize_release_candidate_readiness(
        not_ready_payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )
    export_summary = generate_export_summary_from_payload(
        not_ready_payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )
    change_summary = summarize_app_payload_changes(
        previous_ready_payload,
        not_ready_payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    assert readiness["ready"] is False
    assert [check["key"] for check in readiness["checks"]] == [
        "identity_complete",
        "class_level_valid",
        "ability_normalized",
        "notes_or_personality_present",
        "checkpoint_safe_payload_shape",
    ]
    assert [check["ok"] for check in readiness["checks"]] == [False, True, True, False, True]

    assert "Identity: Unnamed | Unspecified | Unspecified | Unspecified" in export_summary
    assert "Notes: None" in export_summary
    assert "Validation Status: missing name" in export_summary
    assert change_summary == [
        "Identity: Elora | Elf | Sage | Neutral Good -> (unnamed) | (unspecified species) | (unspecified background) | (unspecified alignment)",
        "Character Notes: Tracks rumors -> None",
    ]
