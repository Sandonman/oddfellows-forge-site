from cc_v3.persistence import (
    AppShellState,
    AppState,
    BuilderState,
    deserialize_app_state,
    deserialize_builder_state,
    serialize_app_state,
    serialize_builder_state,
)


CLASSES = ["Cleric", "Fighter", "Wizard"]


def test_builder_state_round_trip_preserves_core_builder_fields():
    state = BuilderState(class_name="Wizard", level=7, look_ahead=True)

    payload = serialize_builder_state(state)
    restored = deserialize_builder_state(payload, available_classes=CLASSES)

    assert restored == state


def test_deserialize_builder_state_clamps_and_falls_back_safely():
    payload = {
        "builder": {
            "class_name": "Unknown",
            "level": 99,
            "look_ahead": 1,
        }
    }

    restored = deserialize_builder_state(payload, available_classes=CLASSES)

    assert restored.class_name == "Cleric"
    assert restored.level == 20
    assert restored.look_ahead is True


def test_app_state_round_trip_preserves_shell_and_builder_fields():
    state = AppState(
        shell=AppShellState(
            title_text="Campaign: Icewind Dale",
            status_text="Autosave pending",
            active_tab="Library",
        ),
        builder=BuilderState(class_name="Wizard", level=5, look_ahead=False),
    )

    payload = serialize_app_state(state)
    restored = deserialize_app_state(
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert restored == state


def test_deserialize_app_state_clamps_and_falls_back_safely():
    payload = {
        "shell": {
            "title_text": "",
            "status_text": "",
            "active_tab": "Unknown tab",
        },
        "builder": {
            "class_name": "Nope",
            "level": -12,
            "look_ahead": 1,
        },
    }

    restored = deserialize_app_state(
        payload,
        available_classes=CLASSES,
        available_tabs=("Builder", "Library"),
    )

    assert restored.shell.title_text == "D&D Character Creator V3"
    assert restored.shell.status_text == "Ready"
    assert restored.shell.active_tab == "Builder"
    assert restored.builder == BuilderState(class_name="Cleric", level=1, look_ahead=True)
