"""Tkinter tooltip helpers."""

from __future__ import annotations

import tkinter as tk
from typing import Callable


class Tooltip:
    def __init__(self, widget: tk.Widget, text_getter: Callable[[], str] | str, delay_ms: int = 350) -> None:
        self.widget = widget
        self.text_getter = text_getter
        self.delay_ms = delay_ms
        self.tip_window: tk.Toplevel | None = None
        self._job: str | None = None

        widget.bind("<Enter>", self._schedule, add=True)
        widget.bind("<Leave>", self._hide, add=True)
        widget.bind("<ButtonPress>", self._hide, add=True)

    def _resolve_text(self) -> str:
        if callable(self.text_getter):
            text = self.text_getter()
        else:
            text = self.text_getter
        return text or ""

    def _schedule(self, _event: tk.Event | None = None) -> None:
        self._unschedule()
        self._job = self.widget.after(self.delay_ms, self._show)

    def _unschedule(self) -> None:
        if self._job:
            self.widget.after_cancel(self._job)
            self._job = None

    def _show(self) -> None:
        text = self._resolve_text().strip()
        if not text:
            return
        if self.tip_window is not None:
            return

        x = self.widget.winfo_pointerx() + 12
        y = self.widget.winfo_pointery() + 12
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background="#fff8dc",
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=420,
            padx=8,
            pady=6,
        )
        label.pack()
        self.tip_window = tw

    def _hide(self, _event: tk.Event | None = None) -> None:
        self._unschedule()
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class ListboxTooltip:
    def __init__(self, listbox: tk.Listbox, text_for_item: Callable[[str], str], delay_ms: int = 300) -> None:
        self.listbox = listbox
        self.text_for_item = text_for_item
        self.delay_ms = delay_ms
        self.tip_window: tk.Toplevel | None = None
        self._job: str | None = None
        self._last_item: str | None = None

        listbox.bind("<Motion>", self._on_motion, add=True)
        listbox.bind("<Leave>", self._hide, add=True)
        listbox.bind("<ButtonPress>", self._hide, add=True)

    def _on_motion(self, event: tk.Event) -> None:
        index = self.listbox.nearest(event.y)
        if index < 0:
            self._hide()
            return

        item = self.listbox.get(index)
        if item != self._last_item:
            self._hide()
            self._last_item = item
            self._job = self.listbox.after(self.delay_ms, lambda: self._show(item))

    def _show(self, item: str) -> None:
        text = (self.text_for_item(item) or "").strip()
        if not text:
            return
        if self.tip_window is not None:
            return

        x = self.listbox.winfo_pointerx() + 12
        y = self.listbox.winfo_pointery() + 12
        tw = tk.Toplevel(self.listbox)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background="#fff8dc",
            relief=tk.SOLID,
            borderwidth=1,
            wraplength=430,
            padx=8,
            pady=6,
        )
        label.pack()
        self.tip_window = tw

    def _hide(self, _event: tk.Event | None = None) -> None:
        if self._job:
            self.listbox.after_cancel(self._job)
            self._job = None
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
        self._last_item = None
