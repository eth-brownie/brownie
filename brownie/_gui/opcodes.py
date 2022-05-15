#!/usr/bin/python3


import time
from tkinter import ttk

from brownie.project.sources import is_inside_offset

from .bases import ToggleButton


class OpcodeList(ttk.Treeview):
    def __init__(self, parent, columns, **kwargs):
        self._last = set()
        self._seek_buffer = ""
        self._seek_last = 0
        self._highlighted = set()
        self._frame = ttk.Frame(parent)
        super().__init__(
            self._frame, columns=[i[0] for i in columns[1:]], selectmode="browse", **kwargs
        )
        self.pack(side="left", fill="y")
        self.heading("#0", text=columns[0][0])
        self.column("#0", width=columns[0][1])
        for tag, width in columns[1:]:
            self.heading(tag, text=tag)
            self.column(tag, width=width)

        scroll = ttk.Scrollbar(self._frame)
        scroll.pack(side="right", fill="y")

        self.configure(yscrollcommand=scroll.set)
        scroll.configure(command=self.yview)

        self.tag_configure("NoSource", background="#161616")
        self.bind("<<TreeviewSelect>>", self._select_bind)

        root = self.root = self._root()
        root.bind("j", self._highlight_jumps)
        root.bind("r", self._highlight_revert)
        self.bind("<3>", self._highlight_opcode)
        for i in range(10):
            root.bind(str(i), self._seek)

    def grid(self, *args, **kwargs):
        self._frame.grid(*args, **kwargs)

    def insert(self, values, tags=[]):
        super().insert("", "end", iid=values[0], text=values[0], values=values[1:], tags=tags)

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

    def set_opcodes(self, pcMap):
        self.delete_all()
        for pc, op in [(i, pcMap[i]) for i in sorted(pcMap)]:
            if "path" not in op or (
                op["path"] == pcMap[0]["path"] and op["offset"] == pcMap[0]["offset"]
            ):
                tag = "NoSource"
            else:
                # used to find all the opcodes with the same source offset
                tag = f"{op['path']}:{op['offset'][0]}:{op['offset'][1]}"
            self.insert([str(pc), op["op"]], [tag, op["op"], str(pc)])

    def _select_bind(self, event=None):
        for tag in self._last:
            self.tag_configure(tag, background="", foreground="")
        self._last.clear()
        try:
            pc = self.selection()[0]
        except IndexError:
            return
        pcMap = self.root.pcMap[pc]
        note = self.root.main.note

        console = self.root.main.console
        console.write(f"{pc} {pcMap['op']}")
        if "value" in pcMap:
            console.append(f" {pcMap['value']}")
        if "offset" in pcMap:
            console.append(f"\nOffsets: {pcMap['offset'][0]}, {pcMap['offset'][1]}")

        if pcMap["op"] in ("JUMP", "JUMPI"):
            prev = self._get_prev(pc)
            if self.root.pcMap[prev]["op"] in ("PUSH1", "PUSH2"):
                tag = int(self.root.pcMap[prev]["value"], 16)
                self.tag_configure(tag, foreground="#00ff00")
                self._last.add(tag)
                console.append(f"\nTarget: {tag}")

        if pcMap["op"] == "JUMPDEST":
            targets = _get_targets(self.root.pcMap, pc)
            if targets:
                console.append(f"\nJumps: {', '.join(targets)}")
            else:
                console.append("\nJumps: None")
            for item in targets:
                self.tag_configure(item, foreground="#00ff00")
                self._last.add(item)

        tag = self.item(pc, "tags")[0]
        if tag == "NoSource":
            note.active_frame().clear_highlight()
            return
        self.tag_configure(tag, background="#2a4864")
        self._last.add(tag)
        if "path" not in pcMap:
            note.active_frame().clear_highlight()
            return
        label = self.root.pathMap[pcMap["path"]]
        note.set_active(label)
        note.active_frame().highlight(*pcMap["offset"])

    def _seek(self, event):
        if self._seek_last < time.time() - 1:
            self._seek_buffer = ""
        self._seek_last = time.time()
        self._seek_buffer += event.char
        pc = sorted([int(i) for i in self.root.pcMap])[::-1]
        id_ = next(str(i) for i in pc if i <= int(self._seek_buffer))
        self.selection_set(id_)

    def _highlight_opcode(self, event):
        pc = self.identify_row(event.y)
        op = self.root.pcMap[pc]["op"]
        if op in self._highlighted:
            self.tag_configure(op, foreground="")
            self._highlighted.remove(op)
            return
        self.tag_configure(op, foreground="#dd3333" if op in ("REVERT", "INVALID") else "#dddd33")
        self._highlighted.add(op)

    def _highlight_jumps(self, event):
        try:
            pc = self.selection()[0]
        except IndexError:
            return
        if self.root.pcMap[pc]["op"] not in ("JUMP", "JUMPI"):
            return
        prev = self._get_prev(pc)
        if self.root.pcMap[prev]["op"] in ("PUSH1", "PUSH2"):
            tag = int(self.root.pcMap[prev]["value"], 16)
            self.see(tag)
            self._select_bind()

    def _highlight_revert(self, event):
        if "REVERT" in self._highlighted:
            self.tag_configure("REVERT", foreground="")
            self._highlighted.discard("REVERT")
        else:
            self.tag_configure("REVERT", foreground="#dd3333")
            self._highlighted.add("REVERT")

    def _get_prev(self, pc):
        pc_list = sorted(self.root.pcMap, key=lambda k: int(k), reverse=True)
        return next(i for i in pc_list if int(i) < int(pc))


class ScopingButton(ToggleButton):
    def __init__(self, parent):
        super().__init__(parent, "Scope", "s")
        self.oplist = self.root.main.oplist

    def toggle_on(self):
        try:
            op = self.oplist.selection()[0]
        except IndexError:
            return False
        if self.oplist.item(op, "tags")[0] == "NoSource":
            return False
        pc = self.root.pcMap[op]
        for key, value in sorted(self.root.pcMap.items(), key=lambda k: int(k[0])):
            if (
                "path" not in value
                or value["path"] != pc["path"]
                or not is_inside_offset(value["offset"], pc["offset"])
            ):
                self.oplist.detach(key)
            else:
                self.oplist.move(key, "", key)
        self.oplist.see(op)
        self.root.main.note.apply_scope(*pc["offset"])
        return True

    def toggle_off(self):
        self.root.main.note.clear_scope()
        for i in sorted(self.root.pcMap, key=lambda k: int(k)):
            self.oplist.move(i, "", i)
        if self.oplist.selection():
            self.oplist.see(self.oplist.selection()[0])


def _get_targets(pc_map, pc):
    targets = []
    for key, value in pc_map.items():
        if int(value.get("value", "0"), 16) != int(pc):
            continue
        next_pc = str(int(key) + int(value["op"][4:]) + 1)
        if pc_map[next_pc]["op"] in ("JUMP", "JUMPI"):
            targets.append(next_pc)
    return targets
