#!/usr/bin/python3

import json
from pathlib import Path
from tkinter import ttk

import brownie._config as config
CONFIG = config.CONFIG

class SelectContract(ttk.Combobox):

    def __init__(self, root, parent):
        self._parent = root
        self._build_path = Path(CONFIG['folders']['project']).joinpath('build/contracts')
        super().__init__(parent, state='readonly', font=(None, 16))
        values = []
        for filename in self._build_path.glob('*.json'):
            if json.load(filename.open())['bytecode']:
                values.append(filename.stem)
        self['values'] = sorted(values)
        root.note.set_visible([])
        self.bind("<<ComboboxSelected>>", self._select)

    def _select(self, event):
        self._parent.note.set_visible([])
        compiled = json.load(self._build_path.joinpath(self.get()+'.json').open())
        self.selection_clear()
        for contract in sorted(set(
            i['contract'].split('/')[-1]
            for i in compiled['pcMap'] if i['contract']
        )):
            self._parent.note.show(contract)
        first = compiled['pcMap'][0].copy()
        self._parent.note.set_active(first['contract'].split('/')[-1])
        self._parent.tree.delete_all()
        for op in compiled['pcMap']:
            if (
                op['contract'] == first['contract'] and
                op['start'] == first['start'] and
                op['stop'] == first['stop']
            ):
                op['contract'] = None
            if op['contract']:
                tag = "{0[start]}:{0[stop]}:{0[contract]}".format(op)
            else:
                tag = "NoSource"
            self._parent.tree.insert([str(op['pc']), op['op']], [tag, op['op']])
        self._parent.pcMap = dict((str(i.pop('pc')), i) for i in compiled['pcMap'])
