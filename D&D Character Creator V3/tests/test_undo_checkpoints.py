from cc_v3.persistence import (
    export_app_payload_json,
    export_builder_payload_json,
    import_app_payload_json,
    import_builder_payload_json,
    pop_undo_checkpoint,
    push_app_undo_checkpoint,
    push_builder_undo_checkpoint,
    push_undo_checkpoint,
    read_state_payload,
    write_state_payload,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]


def test_push_pop_undo_checkpoint_behaves_like_lifo_stack():
    stack = ()
    stack = push_undo_checkpoint(stack, {"builder": {"level": 1}}, capacity=5)
    stack = push_undo_checkpoint(stack, {"builder": {"level": 2}}, capacity=5)

    restored, stack = pop_undo_checkpoint(stack)
    assert restored == {"builder": {"level": 2}}

    restored, stack = pop_undo_checkpoint(stack)
    assert restored == {"builder": {"level": 1}}

    restored, stack = pop_undo_checkpoint(stack)
    assert restored is None
    assert stack == ()


def test_push_undo_checkpoint_trims_to_capacity():
    stack = ()
    for level in (1, 2, 3, 4):
        stack = push_undo_checkpoint(stack, {"builder": {"level": level}}, capacity=3)

    assert stack == (
        {"builder": {"level": 2}},
        {"builder": {"level": 3}},
        {"builder": {"level": 4}},
    )


def test_push_undo_checkpoint_deep_copies_payload_to_preserve_checkpoint_immutability():
    payload = {
        "builder": {
            "level": 3,
            "ability_scores": {"STR": 15, "DEX": 14},
        }
    }

    stack = push_undo_checkpoint((), payload, capacity=5)

    payload["builder"]["level"] = 9
    payload["builder"]["ability_scores"]["STR"] = 1

    restored, _ = pop_undo_checkpoint(stack)

    assert restored == {
        "builder": {
            "level": 3,
            "ability_scores": {"STR": 15, "DEX": 14},
        }
    }


def test_push_builder_undo_checkpoint_restores_canonical_payload_deterministically():
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

    stack = push_builder_undo_checkpoint(
        (),
        mixed_payload,
        available_classes=CLASSES,
        capacity=4,
    )

    restored_once, remaining = pop_undo_checkpoint(stack)
    restored_twice, _ = pop_undo_checkpoint(
        push_builder_undo_checkpoint(
            (),
            mixed_payload,
            available_classes=CLASSES,
            capacity=4,
        )
    )

    assert remaining == ()
    assert restored_once == restored_twice
    assert restored_once == {
        "builder": {
            "class_name": "Wizard",
            "level": 20,
            "look_ahead": True,
            "ability_scores": {
                "STR": 30,
                "DEX": 1,
                "CON": 10,
                "INT": 16,
                "WIS": 10,
                "CHA": 10,
            },
            "skill_proficiencies": {
                "Acrobatics": False,
                "Arcana": True,
                "Athletics": False,
                "Perception": False,
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
            "languages": "Common, Elvish",
            "starting_gold": 45,
            "inventory_text": "Rope\nTorch",
            "prepared_spells_text": "Mage Armor\nShield",
        }
    }


def test_push_app_undo_checkpoint_restores_canonical_shell_and_builder_payload():
    mixed_payload = {
        "shell": {"title_text": "", "status_text": "", "active_tab": "Nope"},
        "builder": {
            "class_name": "Unknown",
            "level": 0,
            "look_ahead": True,
            "ability_scores": {"STR": 18, "DEX": 14},
        },
    }

    stack = push_app_undo_checkpoint(
        (),
        mixed_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
        capacity=2,
    )

    restored, remaining = pop_undo_checkpoint(stack)

    assert remaining == ()
    assert restored == {
        "builder": {
            "class_name": "Cleric",
            "level": 1,
            "look_ahead": True,
            "ability_scores": {
                "STR": 18,
                "DEX": 14,
                "CON": 10,
                "INT": 10,
                "WIS": 10,
                "CHA": 10,
            },
            "skill_proficiencies": {
                "Acrobatics": False,
                "Arcana": False,
                "Athletics": False,
                "Perception": False,
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
            "languages": "",
            "starting_gold": 0,
            "inventory_text": "",
            "prepared_spells_text": "",
        },
        "shell": {
            "title_text": "D&D Character Creator V3",
            "status_text": "Ready",
            "active_tab": "Builder",
        },
    }


def test_push_builder_undo_checkpoint_matches_export_import_round_trip_payload():
    mixed_payload = {
        "builder": {
            "class_name": "Wizard",
            "level": "19",
            "look_ahead": 0,
            "ability_scores": {"STR": "31", "DEX": 14, "INT": "16"},
            "skill_proficiencies": {"Arcana": 1, "Perception": ""},
            "languages": " Common, Elvish, Common ",
            "starting_gold": "45",
            "inventory_text": " Rope\n\n Torch ",
            "prepared_spells_text": "Mage Armor\n\nShield\nMage Armor",
        }
    }

    normalized_from_round_trip = import_builder_payload_json(
        export_builder_payload_json(mixed_payload, available_classes=CLASSES),
        available_classes=CLASSES,
    )

    restored, remaining = pop_undo_checkpoint(
        push_builder_undo_checkpoint(
            (),
            mixed_payload,
            available_classes=CLASSES,
            capacity=2,
        )
    )

    assert remaining == ()
    assert restored == normalized_from_round_trip


def test_push_app_undo_checkpoint_matches_export_import_round_trip_payload():
    mixed_payload = {
        "shell": {"title_text": "", "status_text": "", "active_tab": "Nope"},
        "builder": {
            "class_name": "Unknown",
            "level": "99",
            "look_ahead": 1,
            "ability_scores": {"STR": "31", "DEX": -5, "INT": "16"},
            "skill_proficiencies": {"Arcana": "yes", "Perception": ""},
            "languages": " Common, Elvish, Common ",
            "starting_gold": "45",
            "inventory_text": " Rope\n\n Torch ",
            "prepared_spells_text": "Mage Armor\n\nShield\nMage Armor",
        },
    }

    normalized_from_round_trip = import_app_payload_json(
        export_app_payload_json(
            mixed_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
        ),
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    restored, remaining = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            mixed_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=2,
        )
    )

    assert remaining == ()
    assert restored == normalized_from_round_trip


def test_push_app_undo_checkpoint_preserves_character_notes_across_save_load_and_restore(tmp_path):
    mixed_payload = {
        "shell": {"title_text": "", "status_text": "", "active_tab": "Nope"},
        "builder": {
            "class_name": "Unknown",
            "level": "99",
            "look_ahead": "",
            "ability_scores": {"STR": "31", "DEX": -5, "INT": "16"},
            "skill_proficiencies": {"Arcana": "yes", "Perception": ""},
            "character_notes": "  Keep mission log.\n\n  Buy ink.  ",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "45",
            "inventory_text": " Rope\n\n Torch ",
            "prepared_spells_text": "Mage Armor\n\nShield\nMage Armor",
        },
    }

    checkpoint, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            mixed_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )
    )

    target = write_state_payload(tmp_path / "outputs" / "state-with-notes.json", mixed_payload)
    loaded_payload = read_state_payload(target)

    restored_from_loaded, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            loaded_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )
    )

    assert checkpoint["builder"]["character_notes"] == "Keep mission log.\nBuy ink."
    assert restored_from_loaded["builder"]["character_notes"] == "Keep mission log.\nBuy ink."
    assert restored_from_loaded == checkpoint


def test_push_app_undo_checkpoint_matches_save_load_payload_path(tmp_path):
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

    checkpoint, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            mixed_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )
    )

    target = write_state_payload(tmp_path / "outputs" / "state.json", mixed_payload)
    loaded_payload = read_state_payload(target)

    restored_from_loaded, _ = pop_undo_checkpoint(
        push_app_undo_checkpoint(
            (),
            loaded_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )
    )

    assert restored_from_loaded == checkpoint
