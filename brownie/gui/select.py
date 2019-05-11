#!/usr/bin/python3

from tkinter import ttk


class SelectContract(ttk.Combobox):

    def __init__(self, parent, values):
        super().__init__(parent, state='readonly', font=(None, 16))
        self.root = self._root()
        self['values'] = sorted(values)
        self.bind("<<ComboboxSelected>>", self._select)

    def _select(self, event):
        value = self.get()
        self.selection_clear()
        self.root.set_active(value)
