from cc_v3.persistence import (
    concise_equipment_line,
    concise_notes_line,
    concise_trait_line,
    export_app_payload_json,
    import_app_payload_json,
    summarize_release_candidate_readiness,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]
TABS = ("Builder", "Library")


def _cycle_payload(payload: dict, *, cycles: int) -> dict:
    current = payload
    for _ in range(cycles):
        current = import_app_payload_json(
            export_app_payload_json(current, available_classes=CLASSES, available_tabs=TABS),
            available_classes=CLASSES,
            available_tabs=TABS,
        )
    return current


def _readiness_and_concise_lines(payload: dict) -> tuple[list[dict], dict[str, str]]:
    report = summarize_release_candidate_readiness(
        payload,
        available_classes=CLASSES,
        available_tabs=TABS,
    )
    builder = payload["builder"]
    lines = {
        "trait": concise_trait_line(builder.get("trait")),
        "ideal": concise_trait_line(builder.get("ideal")),
        "bond": concise_trait_line(builder.get("bond")),
        "flaw": concise_trait_line(builder.get("flaw")),
        "notes": concise_notes_line(builder.get("character_notes")),
        "equipment": concise_equipment_line(builder.get("starting_gold"), builder.get("inventory_text")),
    }
    return report["checks"], lines


def test_readiness_and_concise_lines_no_drift_after_repeated_cycles_for_clean_payload():
    clean_payload = {
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
            "trait": "Curious and observant",
            "ideal": "Knowledge should be shared",
            "bond": "Archive mentors",
            "flaw": "Overconfident",
            "character_notes": "Keeps meticulous journals.",
            "languages": "Common, Elvish",
            "starting_gold": 24,
            "inventory_text": "Spellbook\nWand\nRations",
            "prepared_spells_text": "Mage Armor\nShield",
        },
    }

    canonical_once = _cycle_payload(clean_payload, cycles=1)
    canonical_after_many = _cycle_payload(clean_payload, cycles=7)

    baseline_checks, baseline_lines = _readiness_and_concise_lines(canonical_once)
    checks_after_many, lines_after_many = _readiness_and_concise_lines(canonical_after_many)

    assert checks_after_many == baseline_checks
    assert lines_after_many == baseline_lines


def test_readiness_and_concise_lines_no_drift_after_repeated_cycles_for_dirty_payload():
    dirty_payload = {
        "shell": {
            "title_text": "D&D Character Creator V3",
            "status_text": "Ready",
            "active_tab": "Builder",
        },
        "builder": {
            "class_name": "Wizard",
            "level": "5",
            "look_ahead": 0,
            "ability_scores": {"STR": "8", "DEX": "14", "INT": "16", "WIS": None, "CHA": "10"},
            "skill_proficiencies": {"Arcana": 1, "Perception": "yes"},
            "character_name": " Elora  ",
            "race_species": "  Elf\n",
            "background": " Sage ",
            "alignment": "Neutral Good\n",
            "trait": "  Curious and observant\n\nsecond line dropped  ",
            "ideal": " Knowledge should be shared ",
            "bond": "  Archive mentors\nArchive mentors\n",
            "flaw": " Overconfident ",
            "character_notes": "\n Keeps meticulous journals.\n\nKeeps meticulous journals.\n",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "24",
            "inventory_text": " Spellbook\nWand\nRations\nWand\n",
            "prepared_spells_text": " Mage Armor\nShield\nShield\n",
        },
    }

    canonical_once = _cycle_payload(dirty_payload, cycles=1)
    canonical_after_many = _cycle_payload(dirty_payload, cycles=7)

    baseline_checks, baseline_lines = _readiness_and_concise_lines(canonical_once)
    checks_after_many, lines_after_many = _readiness_and_concise_lines(canonical_after_many)

    assert checks_after_many == baseline_checks
    assert lines_after_many == baseline_lines
