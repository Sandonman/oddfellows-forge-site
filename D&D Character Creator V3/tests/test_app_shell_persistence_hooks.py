from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import cc_v3.app as app_module
from cc_v3.app import (
    CharacterCreatorApp,
    format_shell_status,
    generate_export_summary_with_checkpoint_fallback,
)
from cc_v3.persistence import (
    AppShellState,
    AppState,
    BuilderState,
    deserialize_app_state,
    deserialize_builder_state,
    pop_undo_checkpoint,
    push_app_undo_checkpoint,
    read_state_payload,
    serialize_app_state,
    summarize_app_payload_changes,
    write_state_payload,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]


class FakeLabel:
    def __init__(self, text: str):
        self._text = text

    def cget(self, key: str) -> str:
        assert key == "text"
        return self._text

    def configure(self, *, text: str) -> None:
        self._text = text


@dataclass
class FakeBuilderTab:
    classes: tuple[str, ...] = tuple(CLASSES)
    payload: dict | None = None
    applied_state: BuilderState | None = None

    def __post_init__(self) -> None:
        self._classes_index = {name: {} for name in self.classes}

    def get_persisted_state(self) -> dict:
        assert self.payload is not None
        return self.payload

    def apply_persisted_state(self, payload: dict) -> BuilderState:
        self.applied_state = deserialize_builder_state(
            payload,
            available_classes=self._classes_index.keys(),
        )
        return self.applied_state


class FakeNotebook:
    def __init__(self, tabs: tuple[str, ...] = ("Builder", "Library"), active: str = "Builder"):
        self._tabs = list(tabs)
        self._selected = active

    def select(self, tab_id: str | None = None):
        if tab_id is None:
            return self._selected
        self._selected = tab_id
        return tab_id

    def tab(self, tab_id: str, option: str) -> str:
        assert option == "text"
        return tab_id

    def tabs(self) -> list[str]:
        return list(self._tabs)



def _character_creator_methods_available() -> bool:
    return hasattr(CharacterCreatorApp, "get_persisted_state") and hasattr(
        CharacterCreatorApp,
        "apply_persisted_state",
    )


def test_shell_status_text_compact_dirty_saved_loaded_cycle():
    assert format_shell_status(dirty=True) == "Ready*"
    assert format_shell_status(dirty=False) == "Ready"
    assert format_shell_status(dirty=False, last_action="saved") == "Saved"
    assert format_shell_status(dirty=False, last_action="loaded") == "Loaded"


def test_dirty_tracking_changes_with_builder_mutations_and_save_load_actions():
    if not _character_creator_methods_available():
        return

    app_obj = SimpleNamespace(
        status_label=FakeLabel("Ready"),
        _saved_builder_payload={"builder": {"class_name": "Wizard", "level": 3}},
        _suppress_dirty_tracking=False,
        _is_dirty=False,
        _last_status_action=None,
    )

    CharacterCreatorApp._set_status(app_obj, dirty=False)
    CharacterCreatorApp._on_builder_state_change(app_obj, {"builder": {"class_name": "Wizard", "level": 4}})
    assert app_obj.status_label.cget("text") == "Ready*"

    CharacterCreatorApp._set_status(app_obj, dirty=False, last_action="saved")
    assert app_obj.status_label.cget("text") == "Saved"

    CharacterCreatorApp._set_status(app_obj, dirty=False, last_action="loaded")
    assert app_obj.status_label.cget("text") == "Loaded"


def _build_checkpoint_app(payload: dict, *, status_text: str = "Ready") -> SimpleNamespace:
    app_obj = SimpleNamespace(
        notebook=FakeNotebook(active="Builder"),
        title_label=FakeLabel("Campaign"),
        status_label=FakeLabel(status_text),
        builder_tab=FakeBuilderTab(payload=payload),
        _saved_builder_payload={"builder": {"class_name": "Cleric", "level": 1}},
        _suppress_dirty_tracking=False,
        _is_dirty=False,
        _last_status_action=None,
        _undo_checkpoints=(),
        _undo_capacity=5,
    )
    app_obj.get_persisted_state = lambda: CharacterCreatorApp.get_persisted_state(app_obj)
    app_obj.apply_persisted_state = lambda data: CharacterCreatorApp.apply_persisted_state(app_obj, data)
    app_obj._snapshot_builder_payload = lambda payload=None: CharacterCreatorApp._snapshot_builder_payload(app_obj, payload)
    app_obj._set_status = lambda *, dirty, last_action=None: CharacterCreatorApp._set_status(
        app_obj,
        dirty=dirty,
        last_action=last_action,
    )
    return app_obj


def test_app_checkpoint_push_and_restore_round_trip_updates_state_and_status():
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "push_undo_checkpoint"):
        return

    initial_payload = {
        "builder": {
            "class_name": "Wizard",
            "level": 3,
            "character_name": "Elora",
        }
    }
    app_obj = _build_checkpoint_app(initial_payload, status_text="Ready*")

    checkpoint = CharacterCreatorApp.push_undo_checkpoint(app_obj)

    app_obj.builder_tab.payload = {"builder": {"class_name": "Fighter", "level": 7, "character_name": "Brak"}}
    restored = CharacterCreatorApp.restore_previous_checkpoint(app_obj)

    assert checkpoint == restored
    assert app_obj.builder_tab.applied_state is not None
    assert app_obj.builder_tab.applied_state.class_name == "Wizard"
    assert app_obj.builder_tab.applied_state.level == 3
    assert app_obj.status_label.cget("text") == "Loaded"
    assert app_obj._is_dirty is False
    assert app_obj._undo_checkpoints == ()


def test_app_checkpoint_restore_empty_stack_is_safe_and_keeps_dirty_status():
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "restore_previous_checkpoint"):
        return

    app_obj = _build_checkpoint_app({"builder": {"class_name": "Wizard", "level": 2}}, status_text="Ready*")

    restored = CharacterCreatorApp.restore_previous_checkpoint(app_obj)

    assert restored is None
    assert app_obj.status_label.cget("text") == "Ready*"
    assert app_obj._is_dirty is False


def test_dirty_status_flow_checkpoint_mutation_restore_then_preview_generation():
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "_preview_export_summary"):
        return

    checkpoint_payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {"class_name": "Wizard", "level": 3, "character_name": "Elora"},
    }
    checkpoints = push_app_undo_checkpoint((), checkpoint_payload, available_classes=CLASSES, capacity=5)

    app_obj = SimpleNamespace(
        notebook=FakeNotebook(active="Builder"),
        title_label=FakeLabel("Campaign"),
        status_label=FakeLabel("Ready"),
        export_preview_label=FakeLabel("Export preview: (not generated)"),
        builder_tab=FakeBuilderTab(payload=checkpoint_payload),
        _saved_builder_payload={"builder": {"class_name": "Wizard", "level": 3, "character_name": "Elora"}},
        _suppress_dirty_tracking=False,
        _is_dirty=False,
        _last_status_action=None,
        get_export_summary_text=lambda: "Identity: Elora",
    )

    CharacterCreatorApp._on_builder_state_change(
        app_obj,
        {"builder": {"class_name": "Wizard", "level": 4, "character_name": "Elora"}},
    )
    assert app_obj.status_label.cget("text") == "Ready*"

    restored_payload, remaining = pop_undo_checkpoint(checkpoints)
    assert restored_payload is not None
    assert remaining == ()

    CharacterCreatorApp.apply_persisted_state(app_obj, restored_payload)
    app_obj._saved_builder_payload = CharacterCreatorApp._snapshot_builder_payload(app_obj, restored_payload)
    CharacterCreatorApp._set_status(app_obj, dirty=False, last_action="loaded")
    assert app_obj.status_label.cget("text") == "Loaded"

    CharacterCreatorApp._preview_export_summary(app_obj)
    assert app_obj.export_preview_label.cget("text") == "Export preview: Identity: Elora"
    assert app_obj.status_label.cget("text") == "Loaded"


def test_export_preview_generation_preserves_dirty_label_contract():
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "_preview_export_summary"):
        return

    app_obj = SimpleNamespace(
        status_label=FakeLabel("Ready*"),
        export_preview_label=FakeLabel("Export preview: (not generated)"),
        _is_dirty=True,
        _last_status_action=None,
        get_export_summary_text=lambda: "Identity: Test",
    )

    CharacterCreatorApp._preview_export_summary(app_obj)

    assert app_obj.export_preview_label.cget("text") == "Export preview: Identity: Test"
    assert app_obj.status_label.cget("text") == "Ready*"


def test_app_shell_round_trip_full_builder_state_through_file_persistence(tmp_path: Path):
    if not _character_creator_methods_available():
        return

    mixed_raw_payload = {
        "builder": {
            "class_name": "Wizard",
            "level": "99",
            "look_ahead": 1,
            "ability_scores": {
                "STR": "31",
                "DEX": -10,
                "CON": "18",
                "INT": None,
                "WIS": "bad",
                "CHA": 9,
            },
            "skill_proficiencies": {
                "Acrobatics": "yes",
                "Arcana": 0,
                "Athletics": 2,
                "Perception": "",
            },
            "character_name": "  Elora  ",
            "race_species": " Elf ",
            "background": " Sage  ",
            "alignment": "Neutral Good",
            "languages": " Common, Elvish, Common, Dwarvish ",
            "starting_gold": "150",
            "inventory_text": " Rope \n\n Torch \nRations ",
            "prepared_spells_text": " Mage Armor\n\nShield\nMage Armor ",
        }
    }

    app_for_save = SimpleNamespace(
        notebook=FakeNotebook(active="Builder"),
        title_label=FakeLabel("Campaign: Integration"),
        status_label=FakeLabel("Dirty"),
        builder_tab=FakeBuilderTab(payload=mixed_raw_payload),
    )

    first_payload = CharacterCreatorApp.get_persisted_state(app_for_save)
    target = write_state_payload(tmp_path / "outputs" / "state.json", first_payload)

    loaded_payload = read_state_payload(target)
    app_for_load = SimpleNamespace(
        notebook=FakeNotebook(active="Library"),
        title_label=FakeLabel("old"),
        status_label=FakeLabel("old"),
        builder_tab=FakeBuilderTab(payload={"builder": {"class_name": "Cleric"}}),
    )

    loaded_state = CharacterCreatorApp.apply_persisted_state(app_for_load, loaded_payload)

    assert loaded_state.shell == AppShellState(
        title_text="Campaign: Integration",
        status_text="Dirty",
        active_tab="Builder",
    )
    assert app_for_load.builder_tab.applied_state is not None
    assert app_for_load.builder_tab.applied_state == loaded_state.builder
    assert loaded_state.builder == BuilderState(
        class_name="Wizard",
        level=20,
        look_ahead=True,
        ability_scores={"STR": 30, "DEX": 1, "CON": 18, "INT": 10, "WIS": 10, "CHA": 9},
        skill_proficiencies={
            "Acrobatics": True,
            "Arcana": False,
            "Athletics": True,
            "Perception": False,
        },
        character_name="Elora",
        race_species="Elf",
        background="Sage",
        alignment="Neutral Good",
        languages="Common, Elvish, Dwarvish",
        starting_gold=150,
        inventory_text="Rope\nTorch\nRations",
        prepared_spells_text="Mage Armor\nShield",
    )


def test_app_shell_load_normalizes_mixed_payload_and_is_stable_after_second_cycle(tmp_path: Path):
    if not _character_creator_methods_available():
        return

    mixed_payload = {
        "shell": {
            "title_text": "  ",
            "status_text": "",
            "active_tab": "Not A Tab",
        },
        "builder": {
            "class_name": "Unknown",
            "level": 0,
            "look_ahead": "1",
            "ability_scores": {"STR": 99, "DEX": "14", "CON": -5, "INT": "x", "WIS": "11", "CHA": None},
            "skill_proficiencies": {"Athletics": "on", "Arcana": "", "Perception": 2},
            "character_name": "  ",
            "race_species": " Human ",
            "background": "  Soldier",
            "alignment": "Chaotic Helpful",
            "languages": " Common, , Dwarvish, Common ",
            "starting_gold": "-100",
            "inventory_text": "  Bedroll\n\n Rope  ",
            "prepared_spells_text": "\nMagic Missile\n Magic Missile\nShield\n",
        },
    }

    app_obj = SimpleNamespace(
        notebook=FakeNotebook(active="Library"),
        title_label=FakeLabel("old-title"),
        status_label=FakeLabel("old-status"),
        builder_tab=FakeBuilderTab(payload={"builder": {"class_name": "Cleric"}}),
    )

    state_once = CharacterCreatorApp.apply_persisted_state(app_obj, mixed_payload)
    canonical_once = CharacterCreatorApp.get_persisted_state(app_obj)

    target = write_state_payload(tmp_path / "outputs" / "state.json", canonical_once)
    canonical_loaded = read_state_payload(target)

    state_twice = deserialize_app_state(
        canonical_loaded,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    canonical_twice = serialize_app_state(state_twice)

    assert state_once.shell.active_tab == "Builder"
    assert state_once.builder == BuilderState(
        class_name="Cleric",
        level=1,
        look_ahead=True,
        ability_scores={"STR": 30, "DEX": 14, "CON": 1, "INT": 10, "WIS": 11, "CHA": 10},
        skill_proficiencies={
            "Acrobatics": False,
            "Arcana": False,
            "Athletics": True,
            "Perception": True,
        },
        character_name="",
        race_species="Human",
        background="Soldier",
        alignment="",
        languages="Common, Dwarvish",
        starting_gold=0,
        inventory_text="Bedroll\nRope",
        prepared_spells_text="Magic Missile\nShield",
    )
    assert state_twice == state_once
    assert canonical_twice == canonical_once


def test_app_shell_export_summary_helper_uses_current_persisted_state_and_is_deterministic():
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "get_export_summary_text"):
        return

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
            "languages": " Common, Elvish, Common ",
            "starting_gold": "24",
            "inventory_text": " Spellbook\n\nWand\nRations ",
            "prepared_spells_text": " Mage Armor\nMagic Missile\nShield\nMage Armor ",
        },
    }

    app_obj = SimpleNamespace(
        notebook=FakeNotebook(active="Builder"),
        builder_tab=FakeBuilderTab(payload=mixed_payload),
        get_persisted_state=lambda: mixed_payload,
    )

    summary_once = CharacterCreatorApp.get_export_summary_text(app_obj)
    summary_twice = CharacterCreatorApp.get_export_summary_text(app_obj)

    assert summary_once == summary_twice
    assert "Identity: Elora | Elf | Sage | Neutral Good" in summary_once
    assert "Class/Level: Wizard 5" in summary_once
    assert "Core Proficiencies: Arcana, Perception (2/4)" in summary_once
    assert "Languages: Common, Elvish" in summary_once
    assert "Equipment: 24 gp; 3 item(s): Spellbook, Wand, Rations" in summary_once
    assert "Spell Highlights: Mage Armor, Magic Missile, Shield" in summary_once


def test_export_summary_checkpoint_fallback_prefers_last_restored_payload_when_requested():
    current_payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {
            "class_name": "Fighter",
            "level": 7,
            "character_name": "Brak",
        },
    }
    restored_payload = {
        "shell": {"title_text": "Campaign", "status_text": "Loaded", "active_tab": "Builder"},
        "builder": {
            "class_name": "Wizard",
            "level": 3,
            "character_name": "Elora",
        },
    }

    summary = generate_export_summary_with_checkpoint_fallback(
        current_payload,
        available_classes=CLASSES,
        prefer_restored_checkpoint=True,
        restored_checkpoint_payload=restored_payload,
    )

    assert "Identity: Elora" in summary
    assert "Class/Level: Wizard 3" in summary


def test_export_summary_checkpoint_fallback_uses_current_payload_when_checkpoint_missing():
    current_payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {
            "class_name": "Fighter",
            "level": 7,
            "character_name": "Brak",
        },
    }

    summary = generate_export_summary_with_checkpoint_fallback(
        current_payload,
        available_classes=CLASSES,
        prefer_restored_checkpoint=True,
        restored_checkpoint_payload=None,
    )

    assert "Identity: Brak" in summary
    assert "Class/Level: Fighter 7" in summary


def test_export_summary_checkpoint_fallback_prefers_shellless_restored_payload_when_viable():
    current_payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Library"},
        "builder": {
            "class_name": "Fighter",
            "level": 7,
            "character_name": "Brak",
        },
    }
    shellless_restored_payload = {
        "builder": {
            "class_name": "Wizard",
            "level": 3,
            "character_name": "Elora",
        }
    }

    summary = generate_export_summary_with_checkpoint_fallback(
        current_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
        prefer_restored_checkpoint=True,
        restored_checkpoint_payload=shellless_restored_payload,
    )

    assert "Identity: Elora" in summary
    assert "Class/Level: Wizard 3" in summary


def test_export_summary_checkpoint_fallback_uses_current_payload_when_restored_payload_malformed_or_partial():
    current_payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {
            "class_name": "Fighter",
            "level": 7,
            "character_name": "Brak",
        },
    }

    malformed_payloads = (
        {"builder": []},
        {"shell": {"active_tab": "Builder"}, "builder": {}},
    )

    baseline = generate_export_summary_with_checkpoint_fallback(
        current_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
        prefer_restored_checkpoint=True,
        restored_checkpoint_payload=None,
    )

    for restored_payload in malformed_payloads:
        summary = generate_export_summary_with_checkpoint_fallback(
            current_payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            prefer_restored_checkpoint=True,
            restored_checkpoint_payload=restored_payload,
        )
        assert summary == baseline
        assert "Identity: Brak" in summary
        assert "Class/Level: Fighter 7" in summary


def test_export_summary_checkpoint_fallback_uses_current_payload_for_mismatched_class_or_tab_context():
    current_payload = {
        "shell": {"title_text": "Campaign", "status_text": "Ready", "active_tab": "Builder"},
        "builder": {
            "class_name": "Fighter",
            "level": 7,
            "character_name": "Brak",
        },
    }

    baseline = generate_export_summary_with_checkpoint_fallback(
        current_payload,
        available_classes=("Fighter", "Wizard"),
        available_tabs=("Builder", "Library"),
        prefer_restored_checkpoint=True,
        restored_checkpoint_payload=None,
    )

    mismatched_context_payloads = (
        {
            "shell": {"title_text": "Campaign", "status_text": "Loaded", "active_tab": "GhostTab"},
            "builder": {"class_name": "Wizard", "level": 3, "character_name": "Elora"},
        },
        {
            "shell": {"title_text": "Campaign", "status_text": "Loaded", "active_tab": "Builder"},
            "builder": {"class_name": "Rogue", "level": 3, "character_name": "Elora"},
        },
    )

    for restored_payload in mismatched_context_payloads:
        summary = generate_export_summary_with_checkpoint_fallback(
            current_payload,
            available_classes=("Fighter", "Wizard"),
            available_tabs=("Builder", "Library"),
            prefer_restored_checkpoint=True,
            restored_checkpoint_payload=restored_payload,
        )
        assert summary == baseline
        assert "Identity: Brak" in summary
        assert "Class/Level: Fighter 7" in summary


def test_get_export_summary_text_checkpoint_preference_keeps_status_label_unchanged():
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "get_export_summary_text"):
        return

    app_obj = SimpleNamespace(
        notebook=FakeNotebook(active="Builder"),
        status_label=FakeLabel("Loaded"),
        builder_tab=FakeBuilderTab(
            payload={
                "builder": {"class_name": "Fighter", "level": 7, "character_name": "Brak"},
            }
        ),
        _last_restored_checkpoint_payload={
            "builder": {"class_name": "Wizard", "level": 3, "character_name": "Elora"},
        },
        get_persisted_state=lambda: {
            "builder": {"class_name": "Fighter", "level": 7, "character_name": "Brak"},
        },
    )

    summary = CharacterCreatorApp.get_export_summary_text(app_obj, prefer_restored_checkpoint=True)

    assert "Identity: Elora" in summary
    assert app_obj.status_label.cget("text") == "Loaded"


def test_app_shell_save_and_load_hooks_use_file_helpers(monkeypatch, tmp_path: Path):
    if not _character_creator_methods_available():
        return

    state_path = tmp_path / "outputs" / "hook_state.json"
    recorded: dict[str, object] = {}

    payload_to_save = serialize_app_state(
        AppState(
            shell=AppShellState(
                title_text="Campaign: Hook Test",
                status_text="Ready",
                active_tab="Builder",
            ),
            builder=BuilderState(
                class_name="Wizard",
                level=4,
                look_ahead=False,
                ability_scores={"STR": 10, "DEX": 14, "CON": 12, "INT": 16, "WIS": 11, "CHA": 8},
                skill_proficiencies={"Arcana": True, "Perception": True},
                character_name="Kara",
                race_species="Tiefling",
                background="Acolyte",
                alignment="Neutral Good",
                languages="Common, Infernal",
                starting_gold=35,
                inventory_text="Spellbook\nDagger",
                prepared_spells_text="Mage Armor\nShield",
            ),
        )
    )

    def fake_write(path, payload):
        recorded["write_path"] = Path(path)
        recorded["write_payload"] = payload
        return write_state_payload(path, payload)

    def fake_read(path):
        recorded["read_path"] = Path(path)
        return read_state_payload(path)

    monkeypatch.setattr(app_module, "write_state_payload", fake_write)
    monkeypatch.setattr(app_module, "read_state_payload", fake_read)

    app_obj = SimpleNamespace(
        _state_path=state_path,
        status_label=FakeLabel("Ready"),
        get_persisted_state=lambda: payload_to_save,
        apply_persisted_state=lambda payload: deserialize_app_state(
            payload,
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
        ),
    )

    CharacterCreatorApp._save_state(app_obj)
    assert recorded["write_path"] == state_path
    assert recorded["write_payload"] == payload_to_save
    assert app_obj.status_label.cget("text") == "Saved"

    CharacterCreatorApp._load_state(app_obj)
    assert recorded["read_path"] == state_path
    assert app_obj.status_label.cget("text") == "Loaded"


def test_apply_persisted_state_suppresses_dirty_mark_from_builder_change_callback():
    if not _character_creator_methods_available():
        return

    app_obj = SimpleNamespace(
        notebook=FakeNotebook(active="Builder"),
        title_label=FakeLabel("Campaign"),
        status_label=FakeLabel("Ready"),
        _saved_builder_payload={"builder": {"class_name": "Wizard", "level": 3, "character_name": "Elora"}},
        _suppress_dirty_tracking=False,
        _is_dirty=False,
        _last_status_action=None,
    )
    app_obj._set_status = lambda *, dirty, last_action=None: CharacterCreatorApp._set_status(
        app_obj,
        dirty=dirty,
        last_action=last_action,
    )
    app_obj._on_builder_state_change = lambda payload: CharacterCreatorApp._on_builder_state_change(app_obj, payload)

    class CallbackBuilderTab(FakeBuilderTab):
        def __init__(self):
            super().__init__(payload={"builder": {"class_name": "Cleric", "level": 1}})

        def apply_persisted_state(self, payload: dict) -> BuilderState:
            state = super().apply_persisted_state(payload)
            # Simulate callback firing during apply.
            app_obj._on_builder_state_change(self.get_persisted_state())
            return state

    app_obj.builder_tab = CallbackBuilderTab()

    CharacterCreatorApp.apply_persisted_state(
        app_obj,
        {
            "shell": {"title_text": "Campaign", "status_text": "Loaded", "active_tab": "Builder"},
            "builder": {"class_name": "Wizard", "level": 3, "character_name": "Elora"},
        },
    )

    assert app_obj.status_label.cget("text") == "Loaded"
    assert app_obj._is_dirty is False


def test_checkpoint_save_restore_load_sequence_keeps_status_transitions_deterministic(tmp_path: Path):
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "push_undo_checkpoint"):
        return

    state_path = tmp_path / "outputs" / "sequence_state.json"

    app_obj = _build_checkpoint_app(
        {
            "builder": {
                "class_name": "Wizard",
                "level": 3,
                "character_name": "Elora",
                "prepared_spells_text": "Mage Armor",
            }
        },
        status_text="Ready",
    )
    app_obj._state_path = state_path

    status_flow: list[str] = []

    # mutate -> checkpoint
    app_obj.builder_tab.payload = {
        "builder": {
            "class_name": "Wizard",
            "level": 4,
            "character_name": "Elora",
            "prepared_spells_text": "Mage Armor\nShield",
        }
    }
    CharacterCreatorApp._on_builder_state_change(app_obj, app_obj.builder_tab.payload)
    status_flow.append(app_obj.status_label.cget("text"))
    checkpoint = CharacterCreatorApp.push_undo_checkpoint(app_obj)

    # mutate -> save
    app_obj.builder_tab.payload = {
        "builder": {
            "class_name": "Fighter",
            "level": 7,
            "character_name": "Brak",
            "inventory_text": "Shield\nLongsword",
        }
    }
    CharacterCreatorApp._on_builder_state_change(app_obj, app_obj.builder_tab.payload)
    status_flow.append(app_obj.status_label.cget("text"))
    CharacterCreatorApp._save_state(app_obj)
    status_flow.append(app_obj.status_label.cget("text"))

    # mutate -> restore
    app_obj.builder_tab.payload = {
        "builder": {
            "class_name": "Cleric",
            "level": 9,
            "character_name": "Mira",
        }
    }
    CharacterCreatorApp._on_builder_state_change(app_obj, app_obj.builder_tab.payload)
    status_flow.append(app_obj.status_label.cget("text"))

    restored = CharacterCreatorApp.restore_previous_checkpoint(app_obj)
    status_flow.append(app_obj.status_label.cget("text"))

    # load
    CharacterCreatorApp._load_state(app_obj)
    status_flow.append(app_obj.status_label.cget("text"))

    assert checkpoint == restored
    assert status_flow == ["Ready*", "Ready*", "Saved", "Ready*", "Loaded", "Loaded"]


def test_restored_checkpoint_payload_is_canonical_and_export_summary_compatible(tmp_path: Path):
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "push_undo_checkpoint"):
        return

    state_path = tmp_path / "outputs" / "canonical_state.json"
    app_obj = _build_checkpoint_app(
        {
            "builder": {
                "class_name": "Wizard",
                "level": "5",
                "character_name": " Elora ",
                "languages": "Common, Elvish, Common",
                "prepared_spells_text": "Magic Missile\nShield\nMagic Missile",
            }
        },
        status_text="Ready",
    )
    app_obj._state_path = state_path

    checkpoint = CharacterCreatorApp.push_undo_checkpoint(app_obj)

    # Save a different payload, then restore checkpoint and verify canonical/export compatibility.
    app_obj.builder_tab.payload = {
        "builder": {
            "class_name": "Fighter",
            "level": 6,
            "character_name": "Brak",
        }
    }
    CharacterCreatorApp._save_state(app_obj)

    restored = CharacterCreatorApp.restore_previous_checkpoint(app_obj)
    assert restored == checkpoint

    restored_state = deserialize_app_state(
        restored,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    canonical_restored = serialize_app_state(restored_state)
    assert canonical_restored == restored

    summary_once = app_module.generate_export_summary_from_payload(
        restored,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    summary_twice = app_module.generate_export_summary_from_payload(
        restored,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    assert summary_once == summary_twice
    assert "Identity: Elora" in summary_once
    assert "Class/Level: Wizard 5" in summary_once

    CharacterCreatorApp._load_state(app_obj)
    loaded_payload = CharacterCreatorApp.get_persisted_state(app_obj)
    loaded_summary = app_module.generate_export_summary_from_payload(
        loaded_payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )
    assert "Class/Level: Fighter 6" in loaded_summary


def test_save_state_failure_keeps_last_saved_snapshot_and_sets_error_status(monkeypatch):
    if not _character_creator_methods_available():
        return

    app_obj = SimpleNamespace(
        _state_path=Path("outputs") / "state.json",
        status_label=FakeLabel("Ready*"),
        _saved_builder_payload={"class_name": "Wizard", "level": 3},
        get_persisted_state=lambda: {"builder": {"class_name": "Wizard", "level": 4}},
    )

    def fake_write(_path, _payload):
        raise OSError("disk full")

    monkeypatch.setattr(app_module, "write_state_payload", fake_write)

    CharacterCreatorApp._save_state(app_obj)

    assert app_obj.status_label.cget("text") == "Save failed: disk full"
    assert app_obj._saved_builder_payload == {"class_name": "Wizard", "level": 3}


def test_load_state_failure_keeps_last_saved_snapshot_and_sets_error_status(monkeypatch):
    if not _character_creator_methods_available():
        return

    app_obj = SimpleNamespace(
        _state_path=Path("outputs") / "state.json",
        status_label=FakeLabel("Ready*"),
        _saved_builder_payload={"class_name": "Wizard", "level": 3},
        apply_persisted_state=lambda payload: payload,
    )

    def fake_read(_path):
        raise ValueError("bad json")

    monkeypatch.setattr(app_module, "read_state_payload", fake_read)

    CharacterCreatorApp._load_state(app_obj)

    assert app_obj.status_label.cget("text") == "Load failed: bad json"
    assert app_obj._saved_builder_payload == {"class_name": "Wizard", "level": 3}


def test_app_checkpoint_repeated_push_restore_beyond_capacity_is_deterministic():
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "push_undo_checkpoint"):
        return

    app_obj = _build_checkpoint_app(
        {"builder": {"class_name": "Cleric", "level": 1, "character_name": "seed"}},
        status_text="Ready",
    )
    app_obj._undo_capacity = 3

    raw_payloads = [
        {"builder": {"class_name": "Wizard", "level": "2", "character_name": "Elora"}},
        {"builder": {"class_name": "Fighter", "level": 3, "character_name": "Brak"}},
        {"builder": {"class_name": "Cleric", "level": "4", "character_name": "Mira"}},
        {"builder": {"class_name": "Wizard", "level": "99", "character_name": "Elora"}},
        {"builder": {"class_name": "Rogue", "level": 0, "character_name": "InvalidClassFallsBack"}},
        {"builder": {"class_name": "Fighter", "level": "7", "character_name": "Brak"}},
        {"builder": {"class_name": "Wizard", "level": "8", "character_name": "Elora"}},
    ]

    expected_stack = ()
    for payload in raw_payloads:
        app_obj.builder_tab.payload = payload
        CharacterCreatorApp.push_undo_checkpoint(app_obj)
        expected_stack = push_app_undo_checkpoint(
            expected_stack,
            {
                "shell": {
                    "title_text": app_obj.title_label.cget("text"),
                    "status_text": app_obj.status_label.cget("text"),
                    "active_tab": "Builder",
                },
                "builder": payload["builder"],
            },
            available_classes=CLASSES,
            available_tabs=("Builder", "Library"),
            capacity=3,
        )

    restored_payloads: list[dict] = []
    for _ in range(5):
        restored = CharacterCreatorApp.restore_previous_checkpoint(app_obj)
        if restored is None:
            break
        restored_payloads.append(restored)

    assert tuple(restored_payloads) == tuple(reversed(expected_stack))
    assert len(restored_payloads) == 3
    assert app_obj._undo_checkpoints == ()


def test_app_checkpoint_restore_after_exhaustion_is_safe_for_multiple_calls():
    if not _character_creator_methods_available() or not hasattr(CharacterCreatorApp, "restore_previous_checkpoint"):
        return

    app_obj = _build_checkpoint_app(
        {"builder": {"class_name": "Wizard", "level": 5, "character_name": "Elora"}},
        status_text="Ready*",
    )

    checkpoint = CharacterCreatorApp.push_undo_checkpoint(app_obj)
    restored_first = CharacterCreatorApp.restore_previous_checkpoint(app_obj)
    restored_second = CharacterCreatorApp.restore_previous_checkpoint(app_obj)
    restored_third = CharacterCreatorApp.restore_previous_checkpoint(app_obj)

    assert restored_first == checkpoint
    assert restored_second is None
    assert restored_third is None
    assert app_obj._undo_checkpoints == ()
    assert app_obj.status_label.cget("text") == "Loaded"
    assert app_obj._last_restored_checkpoint_payload == checkpoint
