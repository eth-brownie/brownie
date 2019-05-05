#!/usr/bin/python3

from tkinter import ttk

from brownie.project.build import Build
from brownie._config import CONFIG

build = Build()

class SelectContract(ttk.Combobox):

    def __init__(self, root, parent):
        self._parent = root
        super().__init__(parent, state='readonly', font=(None, 16))
        values = []
        for name, data in build.contracts():
            if data['bytecode']:
                values.append(name)
        self['values'] = sorted(values)
        root.note.set_visible([])
        self.bind("<<ComboboxSelected>>", self._select)

    def _select(self, event):
        self._parent.note.set_visible([])
        build_json = build.get_contract(self.get())
        self.selection_clear()
        for contract in sorted(set(
            i['contract'].split('/')[-1]
            for i in build_json['pcMap'] if i['contract']
        )):
            self._parent.note.show(contract)
        first = build_json['pcMap'][0].copy()
        self._parent.note.set_active(first['contract'].split('/')[-1])
        self._parent.tree.delete_all()
        for op in build_json['pcMap']:
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
        self._parent.pcMap = dict((str(i.pop('pc')), i) for i in build_json['pcMap'])
