#!/usr/bin/python3

import tkinter as tk
from tkinter import ttk

from .styles import BUTTON_STYLE


class ToggleButton(tk.Button):
    def __init__(self, parent, text, keybind=None):
        self.active = False
        super().__init__(parent, text=text, command=self.toggle)
        self.root = self._root()
        self.configure(**BUTTON_STYLE)
        if keybind:
            self.root.bind(keybind, self.toggle)

    def toggle(self, event=None):
        if self.active:
            self.toggle_off()
            self.configure(relief="raised", background="#272727")
        else:
            if not self.toggle_on():
                return
            self.configure(relief="sunken", background="#383838")
        self.active = not self.active

    def toggle_on(self):
        pass

    def toggle_off(self):
        pass


class SelectBox(ttk.Combobox):
    def __init__(self, parent, initial, values):
        super().__init__(parent, state="readonly", font=(None, 16))
        self.root = self._root()
        self["values"] = sorted(values)
        self.set(initial)
        self.bind("<<ComboboxSelected>>", self._select)
        self.configure(width=1)

    def _select(self):
        value = self.get()
        self.selection_clear()
        return value
