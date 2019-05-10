#!/usr/bin/python3

from copy import deepcopy
from tkinter import ttk

from brownie.project.build import Build
from brownie._config import CONFIG

build = Build()

class SelectContract(ttk.Combobox):

    def __init__(self, root, parent):
        self._parent = root
        super().__init__(parent, state='readonly', font=(None, 16))
        values = []
        for name, data in build.items():
            if data['bytecode']:
                values.append(name)
        self['values'] = sorted(values)
        root.note.set_visible([])
        self.bind("<<ComboboxSelected>>", self._select)

    def _select(self, event):
        self._parent.note.set_visible([])
        build_json = build[self.get()]
        self.selection_clear()
        for contract in build_json['allSourcePaths']:
            self._parent.note.show(contract)
        pcMap = deepcopy(build_json['pcMap'])
        self._parent.note.set_active(build_json['sourcePath'])
        self._parent.tree.delete_all()
        for pc, op in [(i, pcMap[i]) for i in sorted(pcMap)[1:]]:
            if (
                op['contract'] == pcMap[0]['contract'] and
                op['start'] == pcMap[0]['start'] and
                op['stop'] == pcMap[0]['stop']
            ):
                op['contract'] = None
            if op['contract']:
                tag = "{0[start]}:{0[stop]}:{0[contract]}".format(op)
            else:
                tag = "NoSource"
            self._parent.tree.insert([str(pc), op['op']], [tag, op['op']])
        self._parent.pcMap = dict((str(k),v) for k,v in pcMap.items())
