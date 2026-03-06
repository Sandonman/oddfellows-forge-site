from cc_v3.persistence import BuilderState, deserialize_builder_state, serialize_builder_state


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
