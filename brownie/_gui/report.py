#!/usr/bin/python3

import warnings
from pathlib import Path

from .bases import SelectBox


class ReportSelect(SelectBox):
    def __init__(self, parent):
        super().__init__(parent, "", [])

    def show(self):
        self.grid()

    def hide(self):
        self.grid_remove()

    def set_values(self, contract):
        reports = self._root().reports
        values = []
        for report in sorted(reports):
            if contract in reports[report][report]:
                values.append(report)

        if not values:
            self.set("(No Reports)")
            self.config(state="disabled")
            self.root.toolbar.highlight_select.hide()
            return

        self["values"] = ["None"] + values
        self.config(state="readonly")
        if self.root.report_key:
            self.set(self.root.report_key)
            self.root.toolbar.highlight_select.show()
            if self.root.highlight_key:
                self.root.toolbar.highlight_select.update_highlights(self.root.highlight_key)
        else:
            self.set("Select Report")

    def _select(self, event):
        value = super()._select()
        if value != "None" and self.root.report_key == value:
            return
        self.root.toolbar.highlight_select.toggle_off()
        if value == "None":
            self.root.toolbar.highlight_select.hide()
            self.root.report_key = None
            self.set("Select Report")
            return
        self.root.toolbar.highlight_select.show()
        self.root.report_key = value
        self.root.toolbar.highlight_select.set_values(list(self.root.reports[value]["highlights"]))


class HighlightSelect(SelectBox):
    def __init__(self, parent):
        super().__init__(parent, "", [])
        self.note = self.root.main.note
        self.config(state="readonly")

    def set_values(self, values):
        self["values"] = ["None"] + sorted(values)
        self.set("Report Type")

    def show(self):
        self.grid()

    def hide(self):
        self.grid_remove()

    def _select(self, event):
        value = super()._select()
        self.update_highlights(value)

    def update_highlights(self, value):
        self.toggle_off()
        if value == "None":
            self.set("Report Type")
            return
        self.root.highlight_key = value
        contract = Path(self.root.main.note.active_frame()._label).stem.strip()
        if contract not in self.root.active_report[value]:
            return
        report = self.root.active_report[value][contract]
        for path, (start, stop, color, msg) in [(k, x) for k, v in report.items() for x in v]:
            label = self.root.pathMap[path]
            try:
                self.note.mark(label, color, start, stop, msg)
            except StopIteration:
                warnings.warn(f"Report contains data for an unknown contract: {label}")

    def toggle_off(self):
        self.root.highlight_key = None
        self.note.unmark_all("green", "red", "yellow", "orange")
        self.note.unbind_all()
