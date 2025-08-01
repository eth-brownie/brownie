#!/usr/bin/python3

import tkinter as tk
from tkinter import ttk

from brownie._c_constants import json_load
from brownie.project import get_loaded_projects

from .console import Console, ConsoleButton
from .opcodes import OpcodeList, ScopingButton
from .report import HighlightSelect, ReportSelect
from .source import ContractSelect, SourceNoteBook
from .styles import set_style
from .tooltip import ToolTip


class Root(tk.Tk):

    _active = False

    def __init__(self):
        projects = get_loaded_projects()

        if self._active:
            raise SystemError("GUI is already active")
        if not projects:
            raise SystemError("No project loaded")
        if len(projects) > 1:
            raise SystemError("More than one active project")
        Root._active = True

        self.active_project = projects[0]
        self.pcMap = {}

        self.report_key = None
        self.highlight_key = None
        self.reports = {}
        for path in self.active_project._path.glob("reports/*.json"):
            try:
                with path.open() as fp:
                    self.reports[path.stem] = json_load(fp)
            except Exception:
                continue

        super().__init__(className=f" Brownie GUI - {self.active_project._name}")
        self.bind("<Escape>", lambda k: self.destroy())

        # geometry and styling
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, minsize=30)
        self.rowconfigure(1, weight=1)
        set_style(self)

        # main widgets
        self.main = MainFrame(self)
        self.main.grid(row=1, column=0, sticky="nsew")

        # toolbar widgets
        self.toolbar = ToolbarFrame(self, self.active_project)
        self.toolbar.grid(row=0, column=0, sticky="nsew")

    @property
    def active_report(self):
        return self.reports[self.report_key]["highlights"]

    def set_active_contract(self, contract_name):
        build_json = self.active_project._build.get(contract_name)
        self.pathMap = pathMap = build_json["allSourcePaths"]
        self.main.note.set_visible(sorted(pathMap.values()))
        self.main.note.set_active(build_json["sourcePath"])
        pcMap = build_json["pcMap"]
        self.main.oplist.set_opcodes(pcMap)
        self.pcMap = {str(k): pcMap[k] for k in pcMap}
        for value in (v for v in pcMap.values() if "path" in v):
            value_path = value["path"]
            if value_path not in pathMap:
                value_path = pathMap[value_path]

        self.toolbar.report.show()
        self.toolbar.report.set_values(contract_name)

    def destroy(self):
        super().destroy()
        self.quit()
        Root._active = False


class MainFrame(ttk.Frame):
    def __init__(self, root):
        super().__init__(root)

        # geometry
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, minsize=280)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, minsize=24)

        self.oplist = OpcodeList(self, (("pc", 80), ("opcode", 200)))
        self.oplist.grid(row=0, column=1, rowspan=2, sticky="nsew")

        self.note = SourceNoteBook(self)
        self.note.grid(row=0, column=0, sticky="nsew")

        self.console = Console(self)
        self.console.grid(row=1, column=0, sticky="nsew")


class ToolbarFrame(ttk.Frame):
    def __init__(self, root, project):
        super().__init__(root)
        self.root = root

        # geometry
        self.columnconfigure([0, 1], minsize=80)
        self.columnconfigure(7, weight=1)
        self.columnconfigure([8, 9], minsize=200)
        self.columnconfigure(10, minsize=304)

        # toggle buttons
        self.console = ConsoleButton(self)
        self.console.grid(row=0, column=0, sticky="nsew")
        ToolTip(self.console, "Toggle expanded console")

        self.scope = ScopingButton(self)
        self.scope.grid(row=0, column=1, sticky="nsew")
        ToolTip(self.scope, "Filter opcodes to only show those\nrelated to the highlighted source")

        # report selection
        self.highlight_select = HighlightSelect(self)
        self.highlight_select.grid(row=0, column=8, sticky="nsew", padx=10)
        self.highlight_select.hide()
        ToolTip(self.highlight_select, "Select which report highlights to display")

        self.report = ReportSelect(self)
        self.report.grid(row=0, column=9, sticky="nsew", padx=10)
        self.report.hide()
        ToolTip(self.report, "Select a report to overlay onto the source code")

        # contract selection
        self.combo = ContractSelect(
            self, [k for k, v in project._build.items() if v.get("bytecode")]
        )
        self.combo.grid(row=0, column=10, sticky="nsew")
        ToolTip(self.combo, "Select the contract source to view")
