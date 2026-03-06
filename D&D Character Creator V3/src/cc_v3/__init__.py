"""D&D Character Creator V3."""

from .app import CharacterCreatorApp, create_main_window, run_app
from .builder_tab import BuilderTab, attach_builder_tab, format_builder_summary
from .library_tab import LibraryTab, attach_library_tab, format_library_detail, load_library_index
from .leveling import MAX_LEVEL, LevelSnapshot, build_level_snapshot, level_up, load_classes
from .persistence import BuilderState, deserialize_builder_state, serialize_builder_state

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
    "MAX_LEVEL",
    "LevelSnapshot",
    "load_classes",
    "build_level_snapshot",
    "level_up",
    "BuilderState",
    "serialize_builder_state",
    "deserialize_builder_state",
]
