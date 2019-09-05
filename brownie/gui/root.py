#!/usr/bin/python3

import tkinter as tk
from tkinter import ttk

from .buttons import (
    ScopingToggle,
    # ConsoleToggle,
    HighlightsToggle
)
from .listview import ListView
from .select import (
    ContractSelect,
    HighlightSelect,
    ReportSelect,
)
from .styles import (
    set_style,
    TEXT_STYLE
)
from .textbook import TextBook
from .tooltip import ToolTip

from brownie.project import get_loaded_projects


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
        name = self.active_project._name
        super().__init__(className=f" Brownie GUI - {name}")
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
        self.toolbar.grid(row=0, column=0, sticky='nsew')

        self.active_report = False

    def set_active(self, contract_name):
        build_json = self.active_project._build.get(contract_name)
        self.main.note.set_visible(build_json['allSourcePaths'])
        self.main.note.set_active(build_json['sourcePath'])
        self.main.oplist.set_opcodes(build_json['pcMap'])
        self.pcMap = dict((str(k), v) for k, v in build_json['pcMap'].items())
        if self.toolbar.highlight.active:
            self.toolbar.highlight.reset()

    def get_active(self):
        return self.toolbar.combo.get()

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
        self.rowconfigure(1, minsize=30)

        self.oplist = ListView(self, (("pc", 80), ("opcode", 200)))
        self.oplist.grid(row=0, column=1, rowspan=2, sticky="nsew")

        self.note = TextBook(self)
        self.note.grid(row=0, column=0, sticky="nsew")

        self.console = tk.Text(self, height=1)
        self.console.grid(row=1, column=0, sticky="nsew")
        self.console.configure(**TEXT_STYLE)
        self.console.configure(background="#272727")


class ToolbarFrame(ttk.Frame):

    def __init__(self, root, project):
        super().__init__(root)
        self.root = root

        # geometry
        self.columnconfigure([0, 1], minsize=80)
        self.columnconfigure(3, weight=1)
        self.columnconfigure([2, 4], minsize=250)
        self.columnconfigure(5, minsize=304)

        # toggle buttons
        self.scope = ScopingToggle(self)
        self.scope.grid(row=0, column=0, sticky="nsew")
        ToolTip(self.scope, "Filter opcodes to only show those\nrelated to the highlighted source")

        self.highlight = HighlightsToggle(self)
        self.highlight.grid(row=0, column=1, sticky="nsew")
        ToolTip(self.highlight, "Toggle report highlighting")

        # expand console toggle (working but not implemented)
        # self.console = ConsoleToggle(self)
        # self.console.pack(side="left")

        self.highlight_select = HighlightSelect(self)
        self.highlight_select.grid(row=0, column=2, sticky="nsew", padx=10)
        ToolTip(self.highlight_select, "Select a report to display")

        # report selection
        path = project._project_path.joinpath('reports')
        self.report = ReportSelect(self, list(path.glob('**/*.json')))
        self.report.grid(row=0, column=4, sticky="nsew", padx=10)
        ToolTip(self.report, "Select a report to overlay onto source code")

        # contract selection
        self.combo = ContractSelect(self, [k for k, v in project._build.items() if v['bytecode']])
        self.combo.grid(row=0, column=5, sticky="nsew")
        ToolTip(self.combo, "Select the contract source to view")
