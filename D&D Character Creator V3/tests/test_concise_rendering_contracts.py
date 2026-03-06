import inspect

from cc_v3.persistence import (
    concise_equipment_line,
    concise_notes_line,
    concise_trait_line,
    summarize_release_candidate_readiness,
)


def test_concise_helper_signatures_and_keyword_only_contracts():
    trait_sig = inspect.signature(concise_trait_line)
    assert list(trait_sig.parameters) == ["value", "max_len"]
    assert trait_sig.parameters["max_len"].kind is inspect.Parameter.KEYWORD_ONLY

    notes_sig = inspect.signature(concise_notes_line)
    assert list(notes_sig.parameters) == ["value", "max_len"]
    assert notes_sig.parameters["max_len"].kind is inspect.Parameter.KEYWORD_ONLY

    equipment_sig = inspect.signature(concise_equipment_line)
    assert list(equipment_sig.parameters) == [
        "starting_gold",
        "inventory_text",
        "item_limit",
        "item_max_len",
    ]
    assert equipment_sig.parameters["item_limit"].kind is inspect.Parameter.KEYWORD_ONLY
    assert equipment_sig.parameters["item_max_len"].kind is inspect.Parameter.KEYWORD_ONLY

    readiness_sig = inspect.signature(summarize_release_candidate_readiness)
    assert list(readiness_sig.parameters) == ["payload", "available_classes", "available_tabs"]
    assert readiness_sig.parameters["available_classes"].kind is inspect.Parameter.KEYWORD_ONLY
    assert readiness_sig.parameters["available_tabs"].kind is inspect.Parameter.KEYWORD_ONLY


def test_concise_helper_output_contracts_are_deterministic():
    assert concise_trait_line("  Curious and observant\nsecond line ignored  ") == "Curious and observant"
    assert concise_notes_line("\n  Keeps journals.  \n") == "Keeps journals."
    assert concise_equipment_line(12, "Rope\nTorch\nRations\nBedroll") == (
        "12 gp; 4 item(s): Rope, Torch, Rations, … (+1 more)"
    )


def test_readiness_report_minimal_payload_contract():
    report = summarize_release_candidate_readiness(
        {"builder": {"class_name": "Wizard", "level": 1}},
        available_classes=["Wizard", "Cleric"],
    )

    assert report["ready"] is False
    assert [check["key"] for check in report["checks"]] == [
        "identity_complete",
        "class_level_valid",
        "ability_normalized",
        "notes_or_personality_present",
        "checkpoint_safe_payload_shape",
    ]
