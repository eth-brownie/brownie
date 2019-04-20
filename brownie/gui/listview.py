#!/usr/bin/python3


import time
from tkinter import ttk


class ListView(ttk.Treeview):

    def __init__(self, root, parent, columns, **kwargs):
        self._parent = root
        self._last = ""
        self._seek_buffer = ""
        self._seek_last = 0
        self._highlighted = set()
        self._frame = ttk.Frame(parent)
        super().__init__(
            self._frame,
            columns=[i[0] for i in columns[1:]],
            selectmode="browse",
            **kwargs
        )
        super().pack(side="left", fill="y")
        self.heading("#0", text=columns[0][0])
        self.column("#0", width=columns[0][1])
        for tag, width in columns[1:]:
            self.heading(tag, text=tag)
            self.column(tag, width=width)
        scroll=ttk.Scrollbar(self._frame)
        scroll.pack(side="right", fill="y")
        self.configure(yscrollcommand=scroll.set)
        scroll.configure(command=self.yview)
        self.tag_configure("NoSource", background="#272727")
        self.bind("<<TreeviewSelect>>", self._select_bind)
        root.bind("a", self._show_all)
        root.bind("s", self._show_scope)
        root.bind("j", self._highlight_jumps)
        root.bind("r", self._highlight_revert)
        self.bind("<3>", self._highlight_opcode)
        for i in range(10):
            root.bind(str(i), self._seek)

    def pack(self, *args, **kwargs):
        self._frame.pack(*args, **kwargs)

    def insert(self, values, tags=[]):
        super().insert(
            "",
            "end",
            iid=values[0],
            text=values[0],
            values=values[1:],
            tags=tags
        )

    def delete_all(self):
        for item in self.get_children():
            self.delete(item)

    def clear_selection(self):
        self.selection_remove(self.selection())

    def selection_set(self, id_):
        self.see(id_)
        super().selection_set(id_)
        self.focus_set()
        self.focus(id_)

    def _select_bind(self, event):
        self.tag_configure(self._last, background="")
        try:
            pc = self.selection()[0]
        except IndexError:
            return
        pcMap = self._parent.pcMap
        note = self._parent.note
        tag = self.item(pc, 'tags')[0]
        if tag == "NoSource":
            note.active_frame().clear_highlight()
            return
        self.tag_configure(tag, background="#2a4864")
        self._last = tag
        if not pcMap[pc]['contract']:
            note.active_frame().clear_highlight()
            return
        note.set_active(pcMap[pc]['contract'].split('/')[-1])
        note.active_frame().highlight(pcMap[pc]['start'], pcMap[pc]['stop'])

    def _seek(self, event):
        if self._seek_last < time.time() - 1:
            self._seek_buffer = ""
        self._seek_last = time.time()
        self._seek_buffer += event.char
        pc = sorted([int(i) for i in self._parent.pcMap])[::-1]
        id_ = next(str(i) for i in pc if i<=int(self._seek_buffer))
        self.selection_set(id_)

    def _show_all(self, event):
        self._parent.note.clear_scope()
        for i in sorted(self._parent.pcMap, key= lambda k: int(k)):
            self.move(i, '', i)
        if self.selection():
            self.see(self.selection()[0])

    def _show_scope(self, event):
        if not self.selection():
            return
        pc = self._parent.pcMap[self.selection()[0]]
        if not pc['contract']:
            return
        for key, value in sorted(self._parent.pcMap.items(), key= lambda k: int(k[0])):
            if (
                not value['contract'] or value['contract']!=pc['contract'] or
                value['start'] < pc['start'] or value['stop']>pc['stop']
            ):
                self.detach(key)
            else:
                self.move(key, '', key)
        self.see(self.selection()[0])
        self._parent.note.apply_scope(pc['start'], pc['stop'])

    def _highlight_opcode(self, event):
        pc = self.identify_row(event.y)
        op = self._parent.pcMap[pc]['op']
        if op in self._highlighted:
            self.tag_configure(op, foreground='')
            self._highlighted.remove(op)
        else:
            self.tag_configure(
                op,
                foreground="#dddd33" if op!="REVERT" else "#dd3333"
            )
            self._highlighted.add(op)

    def _highlight_jumps(self, event):
        for op in ("JUMP", "JUMPDEST", "JUMPI"):
            if "JUMPI" in self._highlighted:
                self.tag_configure(op, foreground="")
                self._highlighted.discard(op)
            else:
                self.tag_configure(op, foreground="#dddd33")
                self._highlighted.add(op)

    def _highlight_revert(self, event):
        if "REVERT" in self._highlighted:
            self.tag_configure("REVERT", foreground="")
            self._highlighted.discard("REVERT")
        else:
            self.tag_configure("REVERT", foreground="#dd3333")
            self._highlighted.add("REVERT")