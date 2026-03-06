import inspect

from cc_v3.app import (
    generate_export_summary_from_payload,
    generate_export_summary_with_checkpoint_fallback,
)
from cc_v3.builder_tab import format_builder_summary
from cc_v3.export_summary import format_character_export_summary
from cc_v3.leveling import build_level_snapshot
from cc_v3.persistence import (
    AppShellState,
    AppState,
    BuilderState,
    deserialize_app_state,
    deserialize_builder_state,
    pop_undo_checkpoint,
    push_app_undo_checkpoint,
    summarize_app_payload_changes,
)


def test_cross_module_function_signatures_match_current_contracts():
    app_sig = inspect.signature(generate_export_summary_from_payload)
    assert list(app_sig.parameters) == ["payload", "available_classes", "available_tabs"]
    assert app_sig.parameters["available_classes"].kind is inspect.Parameter.KEYWORD_ONLY
    assert app_sig.parameters["available_tabs"].kind is inspect.Parameter.KEYWORD_ONLY

    app_state_sig = inspect.signature(deserialize_app_state)
    assert list(app_state_sig.parameters) == ["payload", "available_classes", "available_tabs"]
    assert app_state_sig.parameters["available_classes"].kind is inspect.Parameter.KEYWORD_ONLY
    assert app_state_sig.parameters["available_tabs"].kind is inspect.Parameter.KEYWORD_ONLY

    fallback_sig = inspect.signature(generate_export_summary_with_checkpoint_fallback)
    assert list(fallback_sig.parameters) == [
        "current_payload",
        "available_classes",
        "available_tabs",
        "prefer_restored_checkpoint",
        "restored_checkpoint_payload",
    ]
    assert fallback_sig.parameters["available_classes"].kind is inspect.Parameter.KEYWORD_ONLY
    assert fallback_sig.parameters["available_tabs"].kind is inspect.Parameter.KEYWORD_ONLY
    assert fallback_sig.parameters["prefer_restored_checkpoint"].kind is inspect.Parameter.KEYWORD_ONLY
    assert fallback_sig.parameters["restored_checkpoint_payload"].kind is inspect.Parameter.KEYWORD_ONLY

    change_summary_sig = inspect.signature(summarize_app_payload_changes)
    assert list(change_summary_sig.parameters) == [
        "previous_payload",
        "current_payload",
        "available_classes",
        "available_tabs",
    ]
    assert change_summary_sig.parameters["available_classes"].kind is inspect.Parameter.KEYWORD_ONLY
    assert change_summary_sig.parameters["available_tabs"].kind is inspect.Parameter.KEYWORD_ONLY

    builder_state_sig = inspect.signature(deserialize_builder_state)
    assert list(builder_state_sig.parameters) == ["payload", "available_classes"]
    assert builder_state_sig.parameters["available_classes"].kind is inspect.Parameter.KEYWORD_ONLY

    export_sig = inspect.signature(format_character_export_summary)
    assert list(export_sig.parameters) == ["state", "validation_issues"]
    assert export_sig.parameters["validation_issues"].kind is inspect.Parameter.KEYWORD_ONLY

    builder_summary_sig = inspect.signature(format_builder_summary)
    assert list(builder_summary_sig.parameters) == [
        "snapshot",
        "look_ahead",
        "character_name",
        "race_species",
        "background",
        "trait",
        "ideal",
        "bond",
        "flaw",
        "character_notes",
        "alignment",
        "ability_scores",
        "skill_proficiencies",
        "languages",
        "starting_gold",
        "inventory_text",
        "prepared_spells_text",
        "level_input",
    ]
    assert builder_summary_sig.parameters["look_ahead"].kind is inspect.Parameter.KEYWORD_ONLY


def test_generate_export_summary_from_payload_default_tabs_contract():
    payload = {
        "builder": {
            "class_name": "Wizard",
            "level": 5,
            "character_name": "Elora",
        }
    }

    summary = generate_export_summary_from_payload(
        payload,
        available_classes={"Wizard", "Cleric"},
    )

    assert "Character Summary" in summary
    assert "Class/Level: Wizard 5" in summary


def test_builder_to_export_contract_uses_same_normalized_builder_fields():
    payload = {
        "builder": {
            "class_name": "Wizard",
            "level": "5",
            "look_ahead": True,
            "ability_scores": {"INT": 16, "DEX": 14, "STR": 8, "CON": 13, "WIS": 12, "CHA": 10},
            "skill_proficiencies": {"Arcana": True, "Perception": True},
            "character_name": "  Elora ",
            "race_species": " Elf ",
            "background": " Sage ",
            "alignment": "Neutral Good",
            "languages": " Common, Elvish, Common ",
            "starting_gold": "24",
            "inventory_text": "Spellbook\n\nWand",
            "prepared_spells_text": "Mage Armor\nShield\nMage Armor",
        }
    }

    state = deserialize_app_state(payload, available_classes=["Wizard", "Cleric"])
    snapshot = build_level_snapshot(state.builder.class_name, state.builder.level, look_ahead=state.builder.look_ahead)

    builder_summary = format_builder_summary(
        snapshot,
        look_ahead=state.builder.look_ahead,
        character_name=state.builder.character_name,
        race_species=state.builder.race_species,
        background=state.builder.background,
        alignment=state.builder.alignment,
        ability_scores=state.builder.ability_scores,
        skill_proficiencies=state.builder.skill_proficiencies,
        languages=state.builder.languages,
        starting_gold=state.builder.starting_gold,
        inventory_text=state.builder.inventory_text,
        prepared_spells_text=state.builder.prepared_spells_text,
    )

    export_summary = format_character_export_summary(
        AppState(
            shell=AppShellState(title_text="T", status_text="Ready", active_tab="Builder"),
            builder=BuilderState(**state.builder.__dict__),
        )
    )

    assert "Identity: Elora | Elf | Sage | Neutral Good" in builder_summary
    assert "Class/Level: Wizard 5" in builder_summary
    assert "Personality: Trait=None | Ideal=None | Bond=None | Flaw=None" in builder_summary
    assert "Derived Combat: Initiative +2 | Passive Perception 14 | Attack Baseline +5 to hit, +2 damage mod (best STR/DEX)" in builder_summary
    assert "Skills: Arcana, Perception (2/4)" in builder_summary
    assert "Prepared Spells Count: 2" in builder_summary

    assert "Identity: Elora | Elf | Sage | Neutral Good" in export_summary
    assert "Class/Level: Wizard 5" in export_summary
    assert "Personality: Trait=None | Ideal=None | Bond=None | Flaw=None" in export_summary
    assert "Derived Combat: Initiative +2 | Passive Perception 14 | Attack Baseline +5 to hit, +2 damage mod (best STR/DEX)" in export_summary
    assert "Core Proficiencies: Arcana, Perception (2/4)" in export_summary
    assert "Spell Highlights: Mage Armor, Shield" in export_summary


def test_checkpoint_and_change_summary_helpers_reject_contract_drift_to_positional_args():
    payload = {"builder": {"class_name": "Wizard", "level": 1}}

    try:
        generate_export_summary_with_checkpoint_fallback(
            payload,
            ["Wizard"],
        )
    except TypeError:
        pass
    else:
        raise AssertionError("available_classes must remain keyword-only for checkpoint fallback helper")

    try:
        summarize_app_payload_changes(payload, payload, ["Wizard"])
    except TypeError:
        pass
    else:
        raise AssertionError("available_classes must remain keyword-only for change summary helper")


def test_checkpoint_and_undo_helpers_keep_default_argument_compatibility():
    current_payload = {
        "shell": {"title_text": "", "status_text": "", "active_tab": "Nope"},
        "builder": {"class_name": "Wizard", "level": 4, "character_name": "Current"},
    }

    summary = generate_export_summary_with_checkpoint_fallback(
        current_payload,
        available_classes=["Wizard", "Cleric"],
        prefer_restored_checkpoint=True,
    )
    assert "Identity: Current" in summary
    assert "Class/Level: Wizard 4" in summary

    stack = push_app_undo_checkpoint(
        (),
        current_payload,
        available_classes=["Wizard", "Cleric"],
        capacity=3,
    )
    restored, remaining = pop_undo_checkpoint(stack)

    assert remaining == ()
    assert restored is not None
    assert restored["shell"]["active_tab"] == "Builder"
