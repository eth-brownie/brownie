#!/usr/bin/python3

import json
from pathlib import Path
import threading

import tkinter as tk
from tkinter import ttk

from .buttons import ScopingToggle, ConsoleToggle
from .listview import ListView
from .textbook import TextBook
from .select import SelectContract
from .styles import set_style, TEXT_STYLE

from brownie.project.build import Build
from brownie.test.coverage import merge_coverage, generate_report
from brownie._config import CONFIG

build = Build()


class Root(tk.Tk):

    _active = threading.Event()

    def __init__(self, report_file=None):
        if not CONFIG['folders']['project']:
            raise SystemError("No project loaded")

        if report_file and not report_file.endswith('.json'):
            report_file += ".json"

        if self._active.is_set():
            raise SystemError("GUI is already active")
        self._active.set()

        super().__init__(className="Opcode Viewer")
        self.bind("<Escape>", lambda k: self.destroy())

        # main widgets
        self.main = MainFrame(self)
        self.main.pack(side="bottom", expand=True, fill="both")

        # toolbar widgets
        self.toolbar = ToolbarFrame(self)
        self.toolbar.pack(side="top", expand="true", fill="both")

        if report_file:
            report_file = Path(report_file).resolve()
            report = json.load(Path(report_file).open())
            print("Report loaded from {}".format(report_file))
        else:
            path = Path(CONFIG['folders']['project']).joinpath('build/coverage')
            coverage_eval = merge_coverage(path.glob('**/*.json'))
            report = generate_report(coverage_eval)
        self._coverage_report = report['highlights']
        self._show_coverage = False
        self.bind("c", self._toggle_coverage)
        set_style(self)

    def _toggle_coverage(self, event):
        active = self.toolbar.combo.get()
        if not active or active not in self._coverage_report:
            return
        if self._show_coverage:
            self.main.note.unmark_all('green', 'red', 'yellow', 'orange')
            self._show_coverage = False
            return
        for path, item in [(k, x) for k, v in self._coverage_report[active].items() for x in v]:
            label = Path(path).name
            self.main.note.mark(label, item[2], item[0], item[1])
        self._show_coverage = True

    def destroy(self):
        super().destroy()
        self.quit()
        self._active.clear()

    def set_active(self, contract_name):
        build_json = build[contract_name]
        self.main.note.set_visible(build_json['allSourcePaths'])
        self.main.note.set_active(build_json['sourcePath'])
        self.main.oplist.set_opcodes(build_json['pcMap'])
        self.pcMap = dict((str(k), v) for k, v in build_json['pcMap'].items())


class MainFrame(ttk.Frame):

    def __init__(self, root):
        super().__init__(root)
        self.oplist = ListView(self, (("pc", 80), ("opcode", 200)))
        self.oplist.configure(height=30)
        self.oplist.pack(side="right", fill="y", expand=True)

        frame = ttk.Frame(self)
        frame.pack(side="left", fill="y", expand=True)
        self.note = TextBook(frame)
        self.note.pack(side="top", fill="both", expand=True)
        self.note.configure(width=920, height=100)
        self.console = tk.Text(frame, height=1)
        self.console.pack(side="bottom", fill="both")
        self.console.configure(**TEXT_STYLE)


class ToolbarFrame(ttk.Frame):

    def __init__(self, root):
        super().__init__(root)
        self.root = root

        # contract selection
        self.combo = SelectContract(self, [k for k, v in build.items() if v['bytecode']])
        self.combo.pack(side="right", anchor="e")
        self.combo.configure(width=23)

        button = ScopingToggle(self)
        button.pack(side="left")

        button = ConsoleToggle(self)
        button.pack(side="left")
