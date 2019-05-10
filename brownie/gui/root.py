#!/usr/bin/python3

import json
from pathlib import Path
import threading

import tkinter as tk
from tkinter import ttk

from .listview import ListView
from .textbook import TextBook
from .select import SelectContract
from .styles import set_style

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

        self.note = TextBook(self)
        self.note.pack(side="left")

        frame = ttk.Frame(self)
        frame.pack(side="right", expand="true", fill="y")

        self.tree = ListView(self, frame, (("pc", 80), ("opcode", 200)), height=30)
        self.tree.pack(side="bottom")

        self.combo = SelectContract(self, frame)
        self.combo.pack(side="top", expand="true", fill="x")

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
        active = self.combo.get()
        if not active or active not in self._coverage_report:
            return
        if self._show_coverage:
            self.note.unmark_all('green', 'red', 'yellow', 'orange')
            self._show_coverage = False
            return
        for path, item in [(k, x) for k, v in self._coverage_report[active].items() for x in v]:
            label = Path(path).name
            self.note.mark(label, item[2], item[0], item[1])
        self._show_coverage = True

    def destroy(self):
        super().destroy()
        self.quit()
        self._active.clear()
