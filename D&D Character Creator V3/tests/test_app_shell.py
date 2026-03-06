from cc_v3 import create_main_window, run_app
from cc_v3.app import DEFAULT_WINDOW_TITLE


def test_app_shell_exports_and_default_title():
    assert callable(create_main_window)
    assert callable(run_app)
    assert DEFAULT_WINDOW_TITLE == "D&D Character Creator V3"
