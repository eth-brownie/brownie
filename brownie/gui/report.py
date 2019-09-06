#!/usr/bin/python3

import json
from pathlib import Path

from .bases import (
    SelectBox,
)


class ReportSelect(SelectBox):

    def __init__(self, parent, report_paths):
        self._reports = {}
        for path in report_paths:
            try:
                with path.open() as fp:
                    self._reports[path.stem] = json.load(fp)
            except Exception:
                continue
        super().__init__(
            parent,
            "Select Report" if self._reports else "(No Reports)",
            ["None"] + sorted(self._reports) if self._reports else []
        )
        if not self._reports:
            self.config(state="disabled")

    def _select(self, event):
        value = super()._select()
        if value != "None" and self.root.active_report == self._reports[value]:
            return
        self.root.toolbar.highlight_select.toggle_off()
        if value == "None":
            self.root.toolbar.highlight_select.hide()
            self.root.active_report = None
            self.set("Select Report")
            return
        self.root.toolbar.highlight_select.show()
        self.root.report_key = None
        self.root.active_report = self._reports[value]
        self.root.toolbar.highlight_select.set_values(list(self._reports[value]['highlights']))


class HighlightSelect(SelectBox):

    def __init__(self, parent):
        super().__init__(parent, "", [])
        self.note = self.root.main.note
        self.config(state="readonly")

    def set_values(self, values):
        self['values'] = ['None'] + sorted(values)
        self.set("Report Type")

    def show(self):
        self.grid()

    def hide(self):
        self.grid_remove()

    def _select(self, event):
        value = super()._select()
        if value == "None":
            self.toggle_off()
            self.set("Report Type")
            return
        if value == self.root.report_key:
            return
        self.root.report_key = value
        self.toggle_off()
        self.toggle_on()

    def toggle_on(self):
        if not self.root.active_report or not self.root.report_key:
            return False
        contract = self.root.get_active()
        if contract not in self.root.active_report['highlights'][self.root.report_key]:
            return False
        report = self.root.active_report['highlights'][self.root.report_key][contract]
        for path, item in [(k, x) for k, v in report.items() for x in v]:
            label = Path(path).name
            self.note.mark(label, item[2], item[0], item[1])
        return True

    def toggle_off(self):
        self.note.unmark_all('green', 'red', 'yellow', 'orange')

