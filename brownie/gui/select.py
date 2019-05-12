#!/usr/bin/python3

import json
from tkinter import ttk


class _Select(ttk.Combobox):

    def __init__(self, parent, initial, values):
        super().__init__(parent, state='readonly', font=(None, 16))
        self.root = self._root()
        self['values'] = sorted(values)
        self.set(initial)
        self.bind("<<ComboboxSelected>>", self._select)

    def _select(self):
        value = self.get()
        self.selection_clear()
        return value


class ContractSelect(_Select):

    def __init__(self, parent, values):
        super().__init__(parent, "Select a Contract", values)

    def _select(self, event):
        value = super()._select()
        self.root.set_active(value)


class ReportSelect(_Select):

    def __init__(self, parent, report_paths):
        self._reports = {}
        for path in report_paths:
            try:
                self._reports[path.stem] = json.load(path.open())
            except Exception:
                continue
        super().__init__(
            parent,
            "Select a Report" if self._reports else "No Available Reports",
            sorted(self._reports)
        )
        if not self._reports:
            self.config(state="disabled")

    def _select(self, event):
        value = super()._select()
        if self.root.active_report == self._reports[value]:
            return
        self.root.active_report = self._reports[value]
        self.root.toolbar.highlight.reset()
