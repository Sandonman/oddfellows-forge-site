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


def format_stats_summary(snapshot: LevelSnapshot) -> str:
    return "\n".join(
        [
            "Stats (Scaffold)",
            "- Ability score editor will land in a later slice.",
            f"- Current class: {snapshot.class_name}",
            f"- Current level: {snapshot.level}",
            f"- Proficiency bonus: +{snapshot.proficiency_bonus}",
        ]
    )


def format_skills_languages_summary(snapshot: LevelSnapshot) -> str:
    return "\n".join(
        [
            "Skills & Languages (Scaffold)",
            "- Skill proficiency picks will be wired in a later slice.",
            "- Language selections are not editable yet.",
            f"- Build context: {snapshot.class_name} level {snapshot.level}",
        ]
    )


def format_equipment_summary(snapshot: LevelSnapshot) -> str:
    return "\n".join(
        [
            "Equipment (Scaffold)",
            "- Starting gear/loadout UI comes next.",
            "- Inventory editing is not available in this slice.",
            f"- Build context: {snapshot.class_name} level {snapshot.level}",
        ]
    )


def format_spells_summary(snapshot: LevelSnapshot) -> str:
    spellcasting = snapshot.spellcasting or "No spellcasting progression for this class/level"
    return "\n".join(
        [
            "Spells (Scaffold)",
            "- Spell selection/preparation editor will be added in a later slice.",
            f"- Spellcasting status: {spellcasting}",
            f"- Build context: {snapshot.class_name} level {snapshot.level}",
        ]
    )


if TK_AVAILABLE:
    class BuilderTab(ttk.Frame):
        """Character builder panel with scaffolds for planned V3 builder sections."""

        def __init__(self, parent: tk.Misc):
            super().__init__(parent, padding=8)
            self._classes_index = load_classes()
            class_names = sorted(self._classes_index.keys())

            default_class = class_names[0] if class_names else ""
            self._class_name = tk.StringVar(value=default_class)
            self._level = tk.IntVar(value=1)
            self._look_ahead = tk.BooleanVar(value=False)

            self.builder_notebook = ttk.Notebook(self)
            self.builder_notebook.pack(fill=tk.BOTH, expand=True)

            self.overview_tab = ttk.Frame(self.builder_notebook, padding=8)
            self.stats_tab = ttk.Frame(self.builder_notebook, padding=8)
            self.skills_languages_tab = ttk.Frame(self.builder_notebook, padding=8)
            self.equipment_tab = ttk.Frame(self.builder_notebook, padding=8)
            self.spells_tab = ttk.Frame(self.builder_notebook, padding=8)

            self.builder_notebook.add(self.overview_tab, text="Overview")
            self.builder_notebook.add(self.stats_tab, text="Stats")
            self.builder_notebook.add(self.skills_languages_tab, text="Skills & Languages")
            self.builder_notebook.add(self.equipment_tab, text="Equipment")
            self.builder_notebook.add(self.spells_tab, text="Spells")

            controls = ttk.Frame(self.overview_tab)
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

            self.summary = tk.Text(self.overview_tab, wrap=tk.WORD, state=tk.DISABLED, height=16)
            summary_scroll = ttk.Scrollbar(self.overview_tab, orient=tk.VERTICAL, command=self.summary.yview)
            self.summary.configure(yscrollcommand=summary_scroll.set)
            self.summary.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            self.stats_summary = tk.StringVar(value="")
            self.skills_languages_summary = tk.StringVar(value="")
            self.equipment_summary = tk.StringVar(value="")
            self.spells_summary = tk.StringVar(value="")

            ttk.Label(self.stats_tab, textvariable=self.stats_summary, justify=tk.LEFT, anchor=tk.NW).pack(
                fill=tk.BOTH,
                expand=True,
            )
            ttk.Label(
                self.skills_languages_tab,
                textvariable=self.skills_languages_summary,
                justify=tk.LEFT,
                anchor=tk.NW,
            ).pack(fill=tk.BOTH, expand=True)
            ttk.Label(self.equipment_tab, textvariable=self.equipment_summary, justify=tk.LEFT, anchor=tk.NW).pack(
                fill=tk.BOTH,
                expand=True,
            )
            ttk.Label(self.spells_tab, textvariable=self.spells_summary, justify=tk.LEFT, anchor=tk.NW).pack(
                fill=tk.BOTH,
                expand=True,
            )

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

            self.summary.configure(state=tk.NORMAL)
            self.summary.delete("1.0", tk.END)
            self.summary.insert("1.0", format_builder_summary(snapshot, look_ahead=look_ahead))
            self.summary.configure(state=tk.DISABLED)

            self.stats_summary.set(format_stats_summary(snapshot))
            self.skills_languages_summary.set(format_skills_languages_summary(snapshot))
            self.equipment_summary.set(format_equipment_summary(snapshot))
            self.spells_summary.set(format_spells_summary(snapshot))


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
