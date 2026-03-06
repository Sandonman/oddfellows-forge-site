from cc_v3.persistence import (
    export_app_payload_json,
    import_app_payload_json,
    summarize_release_candidate_readiness,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]
TABS = ("Builder", "Library")


def _payload() -> dict:
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
            "character_name": "Elora",
            "race_species": "Elf",
            "background": "Sage",
            "alignment": "Neutral Good",
            "trait": "Curious",
            "ideal": "Knowledge should be shared",
            "bond": "Archive",
            "flaw": "Overconfident",
            "character_notes": "Tracks rumors",
            "languages": "Common, Elvish",
            "starting_gold": 24,
            "inventory_text": "Spellbook\nWand\nRations",
            "prepared_spells_text": "Mage Armor\nShield",
        },
    }


def test_release_candidate_readiness_all_green_for_canonical_payload():
    canonical_payload = import_app_payload_json(
        export_app_payload_json(_payload(), available_classes=CLASSES, available_tabs=TABS),
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    report = summarize_release_candidate_readiness(
        canonical_payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    assert report == {
        "ready": True,
        "checks": [
            {"key": "identity_complete", "ok": True, "detail": "Identity fields complete"},
            {"key": "class_level_valid", "ok": True, "detail": "Class and level are valid"},
            {"key": "ability_normalized", "ok": True, "detail": "Ability scores already canonical"},
            {
                "key": "notes_or_personality_present",
                "ok": True,
                "detail": "Notes/personality content present",
            },
            {
                "key": "checkpoint_safe_payload_shape",
                "ok": True,
                "detail": "Payload is canonical and checkpoint-safe",
            },
        ],
    }


def test_release_candidate_readiness_failing_conditions_are_deterministic_and_ordered():
    failing_payload = {
        "shell": {
            "title_text": "D&D Character Creator V3",
            "status_text": "Ready",
            "active_tab": "Builder",
        },
        "builder": {
            "class_name": "Warlock",
            "level": 99,
            "look_ahead": False,
            "ability_scores": {"STR": 99, "DEX": "bad", "CON": -1},
            "skill_proficiencies": {"Arcana": True},
            "character_name": "",
            "race_species": "",
            "background": "",
            "alignment": "",
            "trait": "",
            "ideal": "",
            "bond": "",
            "flaw": "",
            "character_notes": "",
            "languages": "",
            "starting_gold": 0,
            "inventory_text": "",
            "prepared_spells_text": "",
        },
        "extra": {"should": "fail canonical checkpoint shape"},
    }

    report = summarize_release_candidate_readiness(
        failing_payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )

    assert report["ready"] is False
    assert [check["key"] for check in report["checks"]] == [
        "identity_complete",
        "class_level_valid",
        "ability_normalized",
        "notes_or_personality_present",
        "checkpoint_safe_payload_shape",
    ]
    assert [check["ok"] for check in report["checks"]] == [False, False, False, False, False]
    assert [check["detail"] for check in report["checks"]] == [
        "Missing one or more identity fields (name/species/background/alignment)",
        "Class/level must be within available classes and level 1-20",
        "Ability scores require normalization",
        "Add at least one personality field or character notes",
        "Payload differs from canonical app shape",
    ]
