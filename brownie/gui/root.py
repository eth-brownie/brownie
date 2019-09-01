#!/usr/bin/python3

import threading

import tkinter as tk
from tkinter import ttk

from .buttons import (
    ScopingToggle,
    # ConsoleToggle,
    HighlightsToggle
)
from .listview import ListView
from .select import ContractSelect, ReportSelect, HighlightSelect
from .styles import (
    set_style,
    TEXT_STYLE
)
from .textbook import TextBook
from .tooltip import ToolTip

from brownie.project import get_loaded_projects


class Root(tk.Tk):

    _active = threading.Event()

    def __init__(self):
        projects = get_loaded_projects()
        if not projects:
            raise SystemError("No project loaded")

        if len(projects) > 1:
            raise SystemError("More than one active project")

        if self._active.is_set():
            raise SystemError("GUI is already active")
        self._active.set()

        self._project = projects[0]
        name = self._project._name
        super().__init__(className=f" Brownie GUI - {name}")
        self.bind("<Escape>", lambda k: self.destroy())

        # geometry
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, minsize=30)
        self.rowconfigure(1, weight=1)

        # main widgets
        self.main = MainFrame(self)
        self.main.grid(row=1, column=0, sticky="nsew")

        # toolbar widgets
        self.toolbar = ToolbarFrame(self, self._project)
        self.toolbar.grid(row=0, column=0, sticky='nsew')

        self.active_report = False
        set_style(self)

    def set_active(self, contract_name):
        build_json = self._project._build.get(contract_name)
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
        self._active.clear()


class MainFrame(ttk.Frame):

    def __init__(self, root):
        super().__init__(root)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, minsize=280)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, minsize=30)

        self.oplist = ListView(self, (("pc", 80), ("opcode", 200)))
        self.oplist.grid(row=0, column=1, rowspan=2, sticky="nsew")

        self.note = TextBook(self)
        self.note.grid(row=0, column=0, sticky="nsew")

        # TODO - clean this up
        self.console = tk.Text(self, height=1)
        self.console.grid(row=1, column=0, sticky="nsew")
        self.console.configure(**TEXT_STYLE)
        self.console.configure(background="#272727")


class ToolbarFrame(ttk.Frame):

    def __init__(self, root, project):
        super().__init__(root)
        self.root = root

        # contract selection
        self.combo = ContractSelect(self, [k for k, v in project._build.items() if v['bytecode']])
        self.combo.pack(side="right", anchor="e")
        self.combo.configure(width=23)
        ToolTip(self.combo, "Select the contract source to view")

        path = project._project_path.joinpath('reports')

        self.report = ReportSelect(self, list(path.glob('**/*.json')))
        self.report.pack(side="right", anchor="e", padx=10)
        self.report.configure(width=20)
        ToolTip(self.report, "Select a report to overlay onto source code")

        self.scope = ScopingToggle(self)
        self.scope.pack(side="left")
        ToolTip(self.scope, "Filter opcodes to only show those\nrelated to the highlighted source")

        # self.console = ConsoleToggle(self)
        # self.console.pack(side="left")

        self.highlight = HighlightsToggle(self)
        self.highlight.pack(side="left")
        ToolTip(self.highlight, "Toggle report highlighting")

        self.highlight_select = HighlightSelect(self)
        self.highlight_select.pack(side="left", padx=10)
        ToolTip(self.highlight_select, "Toggle report highlighting")
