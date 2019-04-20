#!/usr/bin/python3

import json
from pathlib import Path
import re
import threading

import tkinter as tk
from tkinter import ttk

from .listview import ListView
from .textbook import TextBook
from .select import SelectContract
from .styles import set_style

from brownie.test.coverage import merge_coverage
import brownie._config as config
CONFIG = config.CONFIG


class Root(tk.Tk):

    _active = threading.Event()

    def __init__(self):
        if not CONFIG['folders']['project']:
            raise SystemError("No project loaded")

        if self._active.is_set():
            raise SystemError("GUI is already active")
        self._active.set()

        super().__init__(className="Opcode Viewer")
        self.bind("<Escape>", lambda k: self.destroy())

        path = Path(CONFIG['folders']['project'])
        self.coverage_folder = path.joinpath('build/coverage')
        self.build_folder = path.joinpath('build/contracts')

        self.note = TextBook(self)
        self.note.pack(side="left")

        frame = ttk.Frame(self)
        frame.pack(side="right", expand="true", fill="y")
        
        self.tree = ListView(self, frame, (("pc", 80), ("opcode", 200)), height=30)
        self.tree.pack(side="bottom")

        self.combo = SelectContract(self, frame)
        self.combo.pack(side="top", expand="true", fill="x")

        self._show_coverage = False
        self.bind("c", self._toggle_coverage)
        set_style(self)

    def _toggle_coverage(self, event):
        active = self.combo.get()
        if not active:
            return
        if self._show_coverage:
            self.note.unmark_all('green', 'red', 'yellow', 'orange')
            self._show_coverage = False
            return
        frame_path = self.note.active_frame()._path
        coverage_files = self.coverage_folder.glob('**/*.json')
        try:
            coverage = merge_coverage(coverage_files)[active][frame_path]
        except KeyError:
            return
        build = json.load(self.build_folder.joinpath(active+'.json').open())
        source = build['source']
        coverage_map = build['coverageMap'][frame_path]
        label = frame_path.split('/')[-1]
        self._show_coverage = True
        for key, fn, lines in [(k,v['fn'],v['line']) for k,v in coverage_map.items()]:
            if coverage[key]['pct'] in (0, 1):
                self.note.mark(
                    label,
                    "green" if coverage[key]['pct'] else "red",
                    fn['start'],
                    fn['stop']
                )
                continue
            for i, ln in enumerate(lines):
                if i in coverage[key]['line']:
                    tag = "green"
                elif i in coverage[key]['true']:
                    tag = "yellow" if _evaluate_branch(source, ln) else "orange"
                elif i in coverage[key]['false']:
                    tag = "orange" if _evaluate_branch(source, ln) else "yellow"
                else:
                    tag = "red"
                self.note.mark(label, tag, ln['start'], ln['stop'])

    def destroy(self):
        super().destroy()
        self.quit()
        self._active.clear()


def _evaluate_branch(source, ln):
    start, stop = ln['start'], ln['stop']
    try:
        idx = _maxindex(source[:start])
    except:
        return False

    # remove comments, strip whitespace
    before = source[idx:start]
    for pattern in ('\/\*[\s\S]*?\*\/', '\/\/[^\n]*'):
        for i in re.findall(pattern, before):
            before = before.replace(i, "")
    before = before.strip("\n\t (")

    idx = source[stop:].index(';')+len(source[:stop])
    if idx <= stop:
        return False
    after = source[stop:idx].split()
    after = next((i for i in after if i!=")"),after[0])[0]
    if (
        (before[-2:] == "if" and after=="|") or
        (before[:7] == "require" and after in (")","|"))
    ):
        return True
    return False


def _maxindex(source):
    comp = [i for i in [";", "}", "{"] if i in source]
    return max([source.rindex(i) for i in comp])+1
