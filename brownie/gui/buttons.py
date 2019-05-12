#!/usr/bin/python3

from pathlib import Path
import tkinter as tk

from .styles import BUTTON_STYLE


class _Toggle(tk.Button):

    def __init__(self, parent, text, keybind=None):
        self.active = False
        super().__init__(parent, text=text, command=self.toggle)
        self.root = self._root()
        self.configure(**BUTTON_STYLE)
        if keybind:
            self.root.bind(keybind, self.toggle)

    def toggle(self, event=None):
        if self.active:
            self.toggle_off()
            self.configure(relief="raised", background="#272727")
        else:
            if not self.toggle_on():
                return
            self.configure(relief="sunken", background="#383838")
        self.active = not self.active

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


class HighlightsToggle(_Toggle):

    def __init__(self, parent):
        super().__init__(parent, "Highlights", "h")
        self.note = self.root.main.note

    def toggle_on(self):
        if not self.root.active_report:
            return False
        contract = self.root.get_active()
        if contract not in self.root.active_report['highlights']:
            return False
        report = self.root.active_report['highlights'][contract]
        for path, item in [(k, x) for k, v in report.items() for x in v]:
            label = Path(path).name
            self.note.mark(label, item[2], item[0], item[1])
        return True

    def toggle_off(self):
        self.note.unmark_all('green', 'red', 'yellow', 'orange')

    def reset(self):
        self.toggle_off()
        self.configure(relief="raised", background="#272727")
        self.active = False
        self.toggle()
