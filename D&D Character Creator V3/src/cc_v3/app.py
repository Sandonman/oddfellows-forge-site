from __future__ import annotations

from pathlib import Path
from typing import Any

from .builder_tab import BuilderTab, attach_builder_tab
from .library_tab import LibraryTab, attach_library_tab

try:
    import tkinter as tk
    from tkinter import ttk

    TK_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - depends on runtime image
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    TK_AVAILABLE = False


DEFAULT_WINDOW_TITLE = "D&D Character Creator V3"


if TK_AVAILABLE:
    class CharacterCreatorApp(ttk.Frame):
        """Main V3 shell: top strip + notebook with Builder and Library tabs."""

        def __init__(self, parent: tk.Misc, *, data_dir: Path | None = None):
            super().__init__(parent, padding=8)

            top = ttk.Frame(self)
            top.pack(fill=tk.X, pady=(0, 8))

            self.title_label = ttk.Label(top, text=DEFAULT_WINDOW_TITLE)
            self.title_label.pack(side=tk.LEFT)

            self.status_label = ttk.Label(top, text="Ready")
            self.status_label.pack(side=tk.RIGHT)

            self.notebook = ttk.Notebook(self)
            self.notebook.pack(fill=tk.BOTH, expand=True)

            self.builder_tab: BuilderTab = attach_builder_tab(self.notebook)
            self.library_tab: LibraryTab = attach_library_tab(self.notebook, data_dir=data_dir)


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
