from __future__ import annotations

from typing import Any

from .leveling import MAX_LEVEL, LevelSnapshot, build_level_snapshot, load_classes
from .persistence import BuilderState, deserialize_builder_state, serialize_builder_state

try:
    import tkinter as tk
    from tkinter import ttk

    TK_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - depends on runtime image
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    TK_AVAILABLE = False


def format_builder_summary(snapshot: LevelSnapshot, *, look_ahead: bool) -> str:
    gained = snapshot.gained_features or ["None"]
    visible = snapshot.visible_features or ["None"]
    lines = [
        f"Class: {snapshot.class_name}",
        f"Level: {snapshot.level}",
        f"Proficiency Bonus: +{snapshot.proficiency_bonus}",
        f"Look Ahead: {'On' if look_ahead else 'Off'}",
        "",
        "Gained at this level:",
        *(f"- {item}" for item in gained),
        "",
        "Visible features:",
        *(f"- {item}" for item in visible),
    ]

    if snapshot.spellcasting:
        lines.extend([
            "",
            "Spellcasting:",
            f"- {snapshot.spellcasting}",
        ])

    return "\n".join(lines)


if TK_AVAILABLE:
    class BuilderTab(ttk.Frame):
        """Character builder summary panel wired to leveling controls."""

        def __init__(self, parent: tk.Misc):
            super().__init__(parent, padding=8)
            self._classes_index = load_classes()
            class_names = sorted(self._classes_index.keys())

            default_class = class_names[0] if class_names else ""
            self._class_name = tk.StringVar(value=default_class)
            self._level = tk.IntVar(value=1)
            self._look_ahead = tk.BooleanVar(value=False)

            controls = ttk.Frame(self)
            controls.pack(fill=tk.X, pady=(0, 8))

            ttk.Label(controls, text="Class:").grid(row=0, column=0, sticky=tk.W)
            self.class_box = ttk.Combobox(
                controls,
                textvariable=self._class_name,
                values=class_names,
                state="readonly",
                width=18,
            )
            self.class_box.grid(row=0, column=1, sticky=tk.W, padx=(6, 12))

            ttk.Label(controls, text="Level:").grid(row=0, column=2, sticky=tk.W)
            self.level_spin = ttk.Spinbox(
                controls,
                from_=1,
                to=MAX_LEVEL,
                textvariable=self._level,
                width=5,
                command=self._refresh_summary,
            )
            self.level_spin.grid(row=0, column=3, sticky=tk.W, padx=(6, 12))

            self.look_ahead_check = ttk.Checkbutton(
                controls,
                text="Look Ahead",
                variable=self._look_ahead,
                command=self._refresh_summary,
            )
            self.look_ahead_check.grid(row=0, column=4, sticky=tk.W)

            self.summary = tk.Text(self, wrap=tk.WORD, state=tk.DISABLED, height=18)
            scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.summary.yview)
            self.summary.configure(yscrollcommand=scroll.set)
            self.summary.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)

            self.class_box.bind("<<ComboboxSelected>>", self._refresh_summary)
            self.level_spin.bind("<FocusOut>", self._refresh_summary)
            self.level_spin.bind("<Return>", self._refresh_summary)

            self._refresh_summary()

        def get_persisted_state(self) -> dict[str, Any]:
            state = BuilderState(
                class_name=self._class_name.get(),
                level=self._safe_level(),
                look_ahead=bool(self._look_ahead.get()),
            )
            return serialize_builder_state(state)

        def apply_persisted_state(self, payload: dict[str, Any]) -> BuilderState:
            state = deserialize_builder_state(
                payload,
                available_classes=self._classes_index.keys(),
            )
            self._class_name.set(state.class_name)
            self._level.set(state.level)
            self._look_ahead.set(state.look_ahead)
            self._refresh_summary()
            return state

        def _safe_level(self) -> int:
            try:
                level = int(self._level.get())
            except (ValueError, tk.TclError):
                return 1
            return min(MAX_LEVEL, max(1, level))

        def _refresh_summary(self, _event: tk.Event | None = None) -> None:
            class_name = self._class_name.get()
            if class_name not in self._classes_index:
                return

            level = self._safe_level()
            self._level.set(level)
            look_ahead = bool(self._look_ahead.get())
            snapshot = build_level_snapshot(
                class_name,
                level,
                look_ahead=look_ahead,
                classes_index=self._classes_index,
            )
            text = format_builder_summary(snapshot, look_ahead=look_ahead)

            self.summary.configure(state=tk.NORMAL)
            self.summary.delete("1.0", tk.END)
            self.summary.insert("1.0", text)
            self.summary.configure(state=tk.DISABLED)


    def attach_builder_tab(notebook: ttk.Notebook) -> BuilderTab:
        tab = BuilderTab(notebook)
        notebook.add(tab, text="Builder")
        return tab
else:
    class BuilderTab:  # type: ignore[no-redef]
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("tkinter is not available in this Python runtime")


    def attach_builder_tab(*_args: Any, **_kwargs: Any) -> BuilderTab:  # type: ignore[no-redef]
        raise RuntimeError("tkinter is not available in this Python runtime")
