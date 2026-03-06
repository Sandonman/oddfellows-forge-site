from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import tkinter as tk
    from tkinter import ttk
    TK_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - depends on runtime image
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    TK_AVAILABLE = False


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_library_index(data_dir: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Load spell / magic item / monster data for the Library tab."""
    data_dir = data_dir or DEFAULT_DATA_DIR

    spells = _load_json(data_dir / "spells.json")
    equipment = _load_json(data_dir / "equipment.json")
    monsters = _load_json(data_dir / "monsters.json")

    magic_items = equipment.get("magic_items", []) if isinstance(equipment, dict) else []

    return {
        "Spells": sorted(spells, key=lambda x: (str(x.get("name", "")).lower())),
        "Magic Items": sorted(magic_items, key=lambda x: (str(x.get("name", "")).lower())),
        "Monsters": sorted(monsters, key=lambda x: (str(x.get("name", "")).lower())),
    }


def format_library_detail(kind: str, row: dict[str, Any]) -> str:
    """Render a readable details panel body for a selected library entry."""
    name = row.get("name", "(Unnamed)")

    if kind == "Spells":
        parts = [
            f"Name: {name}",
            f"Level: {row.get('level', '—')}",
            f"School: {row.get('school', '—')}",
            f"Classes: {', '.join(row.get('classes', [])) or '—'}",
            f"Casting Time: {row.get('casting_time', '—')}",
            f"Range: {row.get('range', '—')}",
            f"Components: {row.get('components', '—')}",
            f"Duration: {row.get('duration', '—')}",
            "",
            row.get("description") or row.get("rules_text") or "No description available.",
        ]
        return "\n".join(parts)

    if kind == "Magic Items":
        parts = [
            f"Name: {name}",
            f"Category: {row.get('category', '—')}",
            f"Rarity: {row.get('rarity', '—')}",
            f"Requires Attunement: {row.get('requires_attunement', '—')}",
            "",
            row.get("description") or "No description available.",
        ]
        return "\n".join(parts)

    # Monsters
    parts = [
        f"Name: {name}",
        f"Size: {row.get('size', '—')}",
        f"Type: {row.get('type', '—')}",
        f"Alignment: {row.get('alignment', '—')}",
        f"Armor Class: {row.get('armor_class', '—')} {row.get('armor_desc', '')}".rstrip(),
        f"Hit Points: {row.get('hit_points', '—')} ({row.get('hit_dice', '—')})",
        f"Challenge Rating: {row.get('challenge_rating', '—')}",
        "",
        row.get("desc") or "No description available.",
    ]
    return "\n".join(parts)


if TK_AVAILABLE:
    class LibraryTab(ttk.Frame):
        """Simple live-wired Library tab: list on left, details pane on right."""

        def __init__(self, parent: tk.Misc, data_dir: Path | None = None):
            super().__init__(parent, padding=8)

            self._index = load_library_index(data_dir)
            self._current_kind = tk.StringVar(value="Spells")
            self._current_rows: list[dict[str, Any]] = []

            controls = ttk.Frame(self)
            controls.pack(fill=tk.X, pady=(0, 8))

            ttk.Label(controls, text="Library:").pack(side=tk.LEFT)
            for kind in ("Spells", "Magic Items", "Monsters"):
                ttk.Radiobutton(
                    controls,
                    text=kind,
                    value=kind,
                    variable=self._current_kind,
                    command=self._reload_list,
                ).pack(side=tk.LEFT, padx=(8, 0))

            body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
            body.pack(fill=tk.BOTH, expand=True)

            left = ttk.Frame(body)
            right = ttk.Frame(body)
            body.add(left, weight=1)
            body.add(right, weight=3)

            self.listbox = tk.Listbox(left, exportselection=False)
            list_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.listbox.yview)
            self.listbox.configure(yscrollcommand=list_scroll.set)
            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            self.details = tk.Text(right, wrap=tk.WORD, state=tk.DISABLED)
            details_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.details.yview)
            self.details.configure(yscrollcommand=details_scroll.set)
            self.details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            details_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            self.listbox.bind("<<ListboxSelect>>", self._on_select)

            self._reload_list()

        def _reload_list(self) -> None:
            kind = self._current_kind.get()
            self._current_rows = self._index.get(kind, [])

            self.listbox.delete(0, tk.END)
            for row in self._current_rows:
                self.listbox.insert(tk.END, row.get("name", "(Unnamed)"))

            self._set_details(f"Select a {kind[:-1].lower()} to view details.")

        def _on_select(self, _event: tk.Event | None = None) -> None:
            sel = self.listbox.curselection()
            if not sel:
                return

            idx = sel[0]
            if idx < 0 or idx >= len(self._current_rows):
                return

            kind = self._current_kind.get()
            row = self._current_rows[idx]
            self._set_details(format_library_detail(kind, row))

        def _set_details(self, text: str) -> None:
            self.details.configure(state=tk.NORMAL)
            self.details.delete("1.0", tk.END)
            self.details.insert("1.0", text)
            self.details.configure(state=tk.DISABLED)


    def attach_library_tab(notebook: ttk.Notebook, data_dir: Path | None = None) -> LibraryTab:
        """Helper to mount the Library tab into an existing ttk.Notebook."""
        tab = LibraryTab(notebook, data_dir=data_dir)
        notebook.add(tab, text="Library")
        return tab
else:
    class LibraryTab:  # type: ignore[no-redef]
        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("tkinter is not available in this Python runtime")


    def attach_library_tab(*_args: Any, **_kwargs: Any) -> LibraryTab:  # type: ignore[no-redef]
        raise RuntimeError("tkinter is not available in this Python runtime")
