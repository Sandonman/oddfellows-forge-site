from __future__ import annotations

from pathlib import Path
from typing import Any


def format_shell_status(*, dirty: bool, last_action: str | None = None) -> str:
    if dirty:
        return "Ready*"
    if last_action == "saved":
        return "Saved"
    if last_action == "loaded":
        return "Loaded"
    return "Ready"

from .builder_tab import BuilderTab, attach_builder_tab
from .export_summary import format_character_export_summary
from .library_tab import LibraryTab, attach_library_tab
from .persistence import (
    AppShellState,
    AppState,
    DEFAULT_STATE_PATH,
    deserialize_app_state,
    deserialize_builder_state,
    pop_undo_checkpoint,
    push_app_undo_checkpoint,
    read_state_payload,
    serialize_app_state,
    write_state_payload,
)

try:
    import tkinter as tk
    from tkinter import ttk

    TK_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - depends on runtime image
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    TK_AVAILABLE = False


DEFAULT_WINDOW_TITLE = "D&D Character Creator V3"


def generate_export_summary_from_payload(
    payload: dict[str, Any],
    *,
    available_classes: list[str] | tuple[str, ...] | set[str],
    available_tabs: list[str] | tuple[str, ...] = ("Builder", "Library"),
) -> str:
    """Normalize state payload then build a deterministic export summary."""

    normalized_state = deserialize_app_state(
        payload,
        available_classes=available_classes,
        available_tabs=available_tabs,
    )
    return format_character_export_summary(normalized_state)


def _is_viable_restored_checkpoint_payload(
    payload: dict[str, Any] | None,
    *,
    available_classes: list[str] | tuple[str, ...] | set[str],
    available_tabs: list[str] | tuple[str, ...],
) -> bool:
    """Return True when a restored checkpoint payload is safe to use for summary fallback."""

    if not isinstance(payload, dict):
        return False

    builder_payload = payload.get("builder")
    if not isinstance(builder_payload, dict):
        return False

    class_name = builder_payload.get("class_name")
    if not isinstance(class_name, str) or class_name not in set(available_classes):
        return False

    shell_payload = payload.get("shell")
    if isinstance(shell_payload, dict) and "active_tab" in shell_payload:
        active_tab = shell_payload.get("active_tab")
        if not isinstance(active_tab, str) or active_tab not in set(available_tabs):
            return False

    return True


def generate_export_summary_with_checkpoint_fallback(
    current_payload: dict[str, Any],
    *,
    available_classes: list[str] | tuple[str, ...] | set[str],
    available_tabs: list[str] | tuple[str, ...] = ("Builder", "Library"),
    prefer_restored_checkpoint: bool = False,
    restored_checkpoint_payload: dict[str, Any] | None = None,
) -> str:
    """Build export summary from checkpoint payload when explicitly requested, else current state."""

    use_restored_checkpoint = (
        prefer_restored_checkpoint
        and _is_viable_restored_checkpoint_payload(
            restored_checkpoint_payload,
            available_classes=available_classes,
            available_tabs=available_tabs,
        )
    )
    selected_payload = restored_checkpoint_payload if use_restored_checkpoint else current_payload
    return generate_export_summary_from_payload(
        selected_payload,
        available_classes=available_classes,
        available_tabs=available_tabs,
    )


if TK_AVAILABLE:
    class CharacterCreatorApp(ttk.Frame):
        """Main V3 shell: top strip + notebook with Builder and Library tabs."""

        def __init__(self, parent: tk.Misc, *, data_dir: Path | None = None):
            super().__init__(parent, padding=8)
            self._state_path = DEFAULT_STATE_PATH
            self._is_dirty = False
            self._last_status_action: str | None = None
            self._suppress_dirty_tracking = False
            self._undo_checkpoints: tuple[dict[str, Any], ...] = ()
            self._undo_capacity = 20
            self._last_restored_checkpoint_payload: dict[str, Any] | None = None

            top = ttk.Frame(self)
            top.pack(fill=tk.X, pady=(0, 8))

            self.title_label = ttk.Label(top, text=DEFAULT_WINDOW_TITLE)
            self.title_label.pack(side=tk.LEFT)

            self.load_button = ttk.Button(top, text="Load", command=self._load_state)
            self.load_button.pack(side=tk.RIGHT, padx=(6, 0))

            self.save_button = ttk.Button(top, text="Save", command=self._save_state)
            self.save_button.pack(side=tk.RIGHT)

            self.preview_export_button = ttk.Button(top, text="Preview Export", command=self._preview_export_summary)
            self.preview_export_button.pack(side=tk.RIGHT, padx=(6, 0))

            self.status_label = ttk.Label(top, text=format_shell_status(dirty=False))
            self.status_label.pack(side=tk.RIGHT, padx=(0, 8))

            self.export_preview_label = ttk.Label(self, text="Export preview: (not generated)", anchor=tk.W)
            self.export_preview_label.pack(fill=tk.X, pady=(0, 8))

            self.notebook = ttk.Notebook(self)
            self.notebook.pack(fill=tk.BOTH, expand=True)

            self.builder_tab: BuilderTab = attach_builder_tab(
                self.notebook,
                on_state_change=self._on_builder_state_change,
            )
            self.library_tab: LibraryTab = attach_library_tab(self.notebook, data_dir=data_dir)
            self._saved_builder_payload = self._snapshot_builder_payload()

        def _set_status(self, *, dirty: bool, last_action: str | None = None) -> None:
            self._is_dirty = dirty
            self._last_status_action = last_action
            self.status_label.configure(text=format_shell_status(dirty=dirty, last_action=last_action))

        def _snapshot_builder_payload(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
            if hasattr(self, "builder_tab") and getattr(self, "builder_tab") is not None:
                return self.builder_tab.get_persisted_state()
            if isinstance(payload, dict):
                return dict(payload.get("builder", {}))
            return {}

        def _on_builder_state_change(self, payload: dict[str, Any]) -> None:
            if getattr(self, "_suppress_dirty_tracking", False):
                return
            is_dirty = payload != self._saved_builder_payload
            self._set_status(dirty=is_dirty)

        def push_undo_checkpoint(self) -> dict[str, Any]:
            payload = self.get_persisted_state()
            self._undo_checkpoints = push_app_undo_checkpoint(
                getattr(self, "_undo_checkpoints", ()),
                payload,
                available_classes=self.builder_tab._classes_index.keys(),
                available_tabs=[self.notebook.tab(tab_id, "text") for tab_id in self.notebook.tabs()],
                capacity=getattr(self, "_undo_capacity", 20),
            )
            return dict(self._undo_checkpoints[-1])

        def restore_previous_checkpoint(self) -> dict[str, Any] | None:
            restored, remaining = pop_undo_checkpoint(getattr(self, "_undo_checkpoints", ()))
            if restored is None:
                return None

            self.apply_persisted_state(restored)
            self._undo_checkpoints = remaining
            self._last_restored_checkpoint_payload = restored
            self._saved_builder_payload = self._snapshot_builder_payload(restored)
            self._set_status(dirty=False, last_action="loaded")
            return restored

        def _save_state(self) -> None:
            try:
                payload = self.get_persisted_state()
                write_state_payload(self._state_path, payload)
            except Exception as exc:
                self.status_label.configure(text=f"Save failed: {exc}")
                return
            self._saved_builder_payload = self._snapshot_builder_payload(payload)
            self._set_status(dirty=False, last_action="saved")

        def _load_state(self) -> None:
            try:
                payload = read_state_payload(self._state_path)
                self.apply_persisted_state(payload)
            except FileNotFoundError:
                self.status_label.configure(text=f"Load failed: missing {self._state_path}")
                return
            except Exception as exc:
                self.status_label.configure(text=f"Load failed: {exc}")
                return
            self._saved_builder_payload = self._snapshot_builder_payload(payload)
            self._set_status(dirty=False, last_action="loaded")

        def get_export_summary_text(self, *, prefer_restored_checkpoint: bool = False) -> str:
            payload = self.get_persisted_state()
            return generate_export_summary_with_checkpoint_fallback(
                payload,
                available_classes=self.builder_tab._classes_index.keys(),
                available_tabs=[self.notebook.tab(tab_id, "text") for tab_id in self.notebook.tabs()],
                prefer_restored_checkpoint=prefer_restored_checkpoint,
                restored_checkpoint_payload=getattr(self, "_last_restored_checkpoint_payload", None),
            )

        def _preview_export_summary(self) -> None:
            try:
                summary = self.get_export_summary_text()
            except Exception as exc:
                self.status_label.configure(text=f"Export preview failed: {exc}")
                return

            first_line = summary.splitlines()[0] if summary else "(empty)"
            self.export_preview_label.configure(text=f"Export preview: {first_line}")
            self._set_status(dirty=self._is_dirty, last_action=self._last_status_action)
            print(summary)

        def get_persisted_state(self) -> dict[str, Any]:
            selected = self.notebook.select()
            active_tab = self.notebook.tab(selected, "text") if selected else "Builder"
            state = AppState(
                shell=AppShellState(
                    title_text=self.title_label.cget("text"),
                    status_text=self.status_label.cget("text"),
                    active_tab=active_tab,
                ),
                builder=deserialize_builder_state(
                    self.builder_tab.get_persisted_state(),
                    available_classes=self.builder_tab._classes_index.keys(),
                ),
            )
            return serialize_app_state(state)

        def apply_persisted_state(self, payload: dict[str, Any]) -> AppState:
            available_tabs = [self.notebook.tab(tab_id, "text") for tab_id in self.notebook.tabs()]
            state = deserialize_app_state(
                payload,
                available_classes=self.builder_tab._classes_index.keys(),
                available_tabs=available_tabs,
            )

            self.title_label.configure(text=state.shell.title_text)
            self.status_label.configure(text=state.shell.status_text)
            self._suppress_dirty_tracking = True
            try:
                self.builder_tab.apply_persisted_state(payload)
            finally:
                self._suppress_dirty_tracking = False

            for tab_id in self.notebook.tabs():
                if self.notebook.tab(tab_id, "text") == state.shell.active_tab:
                    self.notebook.select(tab_id)
                    break

            return state


    def create_main_window(*, data_dir: Path | None = None) -> tuple[tk.Tk, CharacterCreatorApp]:
        root = tk.Tk()
        root.title(DEFAULT_WINDOW_TITLE)
        root.geometry("1024x720")

        app = CharacterCreatorApp(root, data_dir=data_dir)
        app.pack(fill=tk.BOTH, expand=True)

        return root, app


    def run_app(*, data_dir: Path | None = None) -> None:
        root, _app = create_main_window(data_dir=data_dir)
        root.mainloop()
else:
    class CharacterCreatorApp:  # type: ignore[no-redef]
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("tkinter is not available in this Python runtime")


    def create_main_window(*_args: Any, **_kwargs: Any) -> tuple[Any, CharacterCreatorApp]:  # type: ignore[no-redef]
        raise RuntimeError("tkinter is not available in this Python runtime")


    def run_app(*_args: Any, **_kwargs: Any) -> None:  # type: ignore[no-redef]
        raise RuntimeError("tkinter is not available in this Python runtime")
