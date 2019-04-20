#!/usr/bin/python3

import json
import re

import tkinter as tk
from tkinter import ttk

from lib.listview import ListView
from lib.textbook import TextBook
from lib.select import SelectContract


class Root(tk.Tk):
    
    def __init__(self):
        super().__init__(className="Opcode Viewer")
        self.bind("<Escape>", lambda k: self.quit())

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

    def _toggle_coverage(self, event):
        active = self.combo.get()
        if not active:
            return
        try:
            coverage = json.load(open("build/coverage.json"))[active]
        except FileNotFoundError:
            return
        if self._show_coverage:
            self.note.unmark_all('green', 'red', 'yellow', 'orange')
            self._show_coverage = False
            return
        self._show_coverage = True
        source = Source()
        for i in coverage:
            label = i['contract'].split('/')[-1]
            if not i['count']:
                tag = "red"
            elif not i['jump'] or 0 not in i['jump']:
                tag = "green"
            # if jump[0] is true, the statement resulted in a jump
            elif i['jump'][0]:
                tag = "yellow" if source.evaluate_condition(i) else "orange"
            # if jump[1] is true, the statement did not result in a jump
            else:
                tag = "orange" if source.evaluate_condition(i) else "yellow"
            self.note.mark(label, tag, i['start'], i['stop'])


class Source:

    def __init__(self):
        self._s = {}

    # evaluate surrounding source code to determine if a jump
    # occured because a statement evaluated true or false
    def evaluate_condition(self, op):
        path = op['contract']
        if path not in self._s:
            self._s[path] = open(path).read()
        s = self._s[path]
        try:
            idx = _maxindex(s[:op['start']])
        except:
            return False

        # remove comments, strip whitespace
        before = s[idx:op['start']]
        for pattern in ('\/\*[\s\S]*?\*\/', '\/\/[^\n]*'):
            for i in re.findall(pattern, before):
                before = before.replace(i, "")
        before = before.strip("\n\t (")

        idx = s[op['stop']:].index(';')+len(s[:op['stop']])
        if idx <= op['stop']:
            return False
        after = s[op['stop']:idx].split()
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