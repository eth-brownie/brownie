#!/usr/bin/python3

import tkinter as tk

TOOLTIP_DELAY = 1


class ToolTip(tk.Toplevel):

    def __init__(self, widget, text=None, textvariable=None):
        super().__init__(widget._root())
        label = tk.Label(self, text=text, textvariable=textvariable, font=(None, 10))
        label.pack()
        self.wm_overrideredirect(True)
        self.withdraw()
        self.kill = False
        self.widget = widget
        widget.bind("<Enter>", self.enter)

    def enter(self, event):
        self.kill = False
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<1>", self.leave)
        self.after(int(TOOLTIP_DELAY*1000), self.show)

    def show(self):
        if self.kill:
            return
        self.geometry("+{}+{}".format(
            self.winfo_pointerx()+5,
            self.winfo_pointery()+5
        ))
        self.lift()
        self.deiconify()

    def leave(self, event):
        self.kill = True
        self.widget.unbind("<Leave>")
        self.withdraw()
        self.widget.bind("<Enter>", self.enter)
