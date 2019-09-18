#!/usr/bin/python3

import tkinter as tk

from .bases import ToggleButton
from .styles import TEXT_STYLE


class ConsoleButton(ToggleButton):
    def __init__(self, parent):
        super().__init__(parent, "Console", "c")
        self.console = self.root.main.console

    def toggle_on(self):
        self.console.config(height=3)
        return True

    def toggle_off(self):
        self.console.config(height=1)


class Console(tk.Text):
    def __init__(self, parent):
        super().__init__(parent, height=1)
        self.configure(**TEXT_STYLE)
        self.configure(background="#161616")
        self._content = ""

    def write(self, text):
        self.configure(state="normal")
        self.delete(1.0, "end")
        self.insert(1.0, text)
        self.configure(state="disabled")
        self._content = text

    def append(self, text):
        self.configure(state="normal")
        self.insert("end", text)
        self.configure(state="disabled")
        self._content += text

    def clear(self):
        self.configure(state="normal")
        self.delete(1.0, "end")
        self.configure(state="disabled")
        self._content = ""

    def read(self):
        return self._content
