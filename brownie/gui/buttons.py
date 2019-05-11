#!/usr/bin/python3

import tkinter as tk


class _Toggle(tk.Button):

    def __init__(self, parent, text, keybind=None):
        self._active = False
        super().__init__(parent, text=text, command=self.toggle)
        self.root = self._root()
        if keybind:
            self.root.bind(keybind, self.toggle)

    def toggle(self, event=None):
        if self._active:
            self.toggle_off()
            self.configure(relief="raised")
        else:
            if not self.toggle_on():
                return
            self.configure(relief="sunken")
        self._active = not self._active

    def toggle_on(self):
        pass

    def toggle_off(self):
        pass


class ScopingToggle(_Toggle):

    def __init__(self, parent):
        super().__init__(parent, "Scope", "s")
        self.oplist = self.root.main.oplist

    def toggle_on(self):
        try:
            op = self.oplist.selection()[0]
        except IndexError:
            return False
        if self.oplist.item(op, 'tags')[0] == "NoSource":
            return False
        pc = self.root.pcMap[op]
        for key, value in sorted(self.root.pcMap.items(), key=lambda k: int(k[0])):
            if (
                not value['contract'] or value['contract'] != pc['contract'] or
                value['start'] < pc['start'] or value['stop'] > pc['stop']
            ):
                self.oplist.detach(key)
            else:
                self.oplist.move(key, '', key)
        self.oplist.see(op)
        self.root.main.note.apply_scope(pc['start'], pc['stop'])
        return True

    def toggle_off(self):
        self.root.main.note.clear_scope()
        for i in sorted(self.root.pcMap, key=lambda k: int(k)):
            self.oplist.move(i, '', i)
        if self.oplist.selection():
            self.oplist.see(self.oplist.selection()[0])


class ConsoleToggle(_Toggle):

    def __init__(self, parent):
        super().__init__(parent, "Console", "c")
        self.console = self.root.main.console

    def toggle_on(self):
        self.console.config(height=10)
        return True

    def toggle_off(self):
        self.console.config(height=1)
