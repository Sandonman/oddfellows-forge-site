"""D&D Character Creator V3."""

from .app import CharacterCreatorApp, create_main_window, run_app
from .builder_tab import BuilderTab, attach_builder_tab, format_builder_summary
from .library_tab import LibraryTab, attach_library_tab, format_library_detail, load_library_index
from .export_summary import format_character_export_summary
from .leveling import MAX_LEVEL, LevelSnapshot, build_level_snapshot, level_up, load_classes
from .persistence import (
    AppShellState,
    AppState,
    BuilderState,
    deserialize_app_state,
    deserialize_builder_state,
    export_app_payload_json,
    export_builder_payload_json,
    import_app_payload_json,
    import_builder_payload_json,
    serialize_app_state,
    serialize_builder_state,
    summarize_app_payload_changes,
    summarize_release_candidate_readiness,
)

__all__ = [
    "CharacterCreatorApp",
    "create_main_window",
    "run_app",
    "BuilderTab",
    "attach_builder_tab",
    "format_builder_summary",
    "LibraryTab",
    "attach_library_tab",
    "format_library_detail",
    "load_library_index",
    "format_character_export_summary",
    "MAX_LEVEL",
    "LevelSnapshot",
    "load_classes",
    "build_level_snapshot",
    "level_up",
    "BuilderState",
    "AppShellState",
    "AppState",
    "serialize_builder_state",
    "deserialize_builder_state",
    "serialize_app_state",
    "deserialize_app_state",
    "export_builder_payload_json",
    "import_builder_payload_json",
    "export_app_payload_json",
    "import_app_payload_json",
    "summarize_app_payload_changes",
    "summarize_release_candidate_readiness",
]
