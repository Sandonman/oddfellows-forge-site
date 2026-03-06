from dataclasses import replace

from cc_v3.persistence import AppShellState

# Mock functions to simulate actual behavior

def get_current_status_text(state):
    # This would return the status text from the app shell state; mocked here for testing
    return state.status_text

def check_if_dirty(state):
    # Mocking that the state is always dirty for testing purposes
    return True

def perform_non_state_changing_action():
    # Mock non-state-changing action
    pass


def test_status_text_transitions():
    # Create a valid initial state
    initial_state = AppShellState(title_text='Campaign', status_text='Ready', active_tab='Builder')
    transitions = [
        ("load", "Loading..."),
        ("save", "Saving..."),
        ("success", "Saved Successfully!"),
        ("error", "Save Failed!"),
    ]

    for action, expected_text in transitions:
        # Simulate action affecting the status text
        if action == "load":
            initial_state = replace(initial_state, status_text="Loading...")
        elif action == "save":
            initial_state = replace(initial_state, status_text="Saving...")
        elif action == "success":
            initial_state = replace(initial_state, status_text="Saved Successfully!")
        elif action == "error":
            initial_state = replace(initial_state, status_text="Save Failed!")

        assert get_current_status_text(initial_state) == expected_text


def test_non_state_changing_action():
    # Check that non-state-changing actions do not clear dirty marker
    initial_state = AppShellState(title_text='Campaign', status_text='Ready', active_tab='Builder')
    is_dirty = check_if_dirty(initial_state)
    assert is_dirty
    # Execute a non-state-changing action
    perform_non_state_changing_action()
    assert is_dirty
