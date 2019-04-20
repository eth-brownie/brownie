#!/usr/bin/python3

import json
import os
from tkinter import ttk


class SelectContract(ttk.Combobox):

    def __init__(self, root, parent):
        self._parent = root
        super().__init__(parent, state='readonly', font=(None, 16))
        values = []
        for filename in sorted(os.listdir('build/contracts')):
            if filename[-5:] != '.json':
                continue
            source = _load(filename)
            if source['type'] == "interface":
                continue
            values.append(source['contractName'])
            root.note.add(source['source'], source['sourcePath'].split('/')[-1])
        self['values'] = sorted(values)
        root.note.set_visible([])
        self.bind("<<ComboboxSelected>>", self._select)

    def _select(self, event):
        self._parent.note.set_visible([])
        compiled = _load(self.get()+'.json')
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


def _load(name):
    return json.load(open('build/contracts/'+name))