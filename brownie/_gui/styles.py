#!/usr/bin/python3

from tkinter import ttk

TEXT_STYLE = {
    "font": ("Courier", 14),
    "background": "#383838",
    "foreground": "#FFFFFF",
    "selectforeground": "white",
    "selectbackground": "#4a6984",
    "inactiveselectbackground": "#4a6984",
    "borderwidth": 0,
    "highlightthickness": 0,
    "state": "disabled",
}

# if these colors are changed, please also update docs/gui.rst
TEXT_COLORS = {
    "comment": {"foreground": "#868686"},
    "dark": {"background": "#272727", "foreground": "#A9A9A9"},
    "red": {"background": "#882222", "foreground": "#FFFFFF"},
    "green": {"background": "#228822", "foreground": "#FFFFFF"},
    "orange": {"background": "#FF3300", "foreground": "#FFFFFF"},
    "yellow": {"background": "#FF9933", "foreground": "#FFFFFF"},
}


BUTTON_STYLE = {
    "borderwidth": 1,
    "background": "#272727",
    "foreground": "#ECECEC",
    "highlightthickness": 0,
    "activebackground": "#383838",
    "activeforeground": "white",
    "width": 1,
}


def set_style(root):

    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Treeview",
        background="#272727",
        fieldbackground="#383838",
        foreground="#ECECEC",
        font=(None, 16),
        rowheight=26,
        height=1,
        borderwidth=0,
        relief="flat",
    )
    style.configure(
        "Treeview.Heading",
        background="#161616",
        foreground="#ECECEC",
        borderwidth=2,
        font=(None, 16),
        relief="flat",
    )
    style.map(
        "Treeview.Heading",
        background=[("active", "#383838"), ("selected", "#383838")],
        foreground=[("active", "#ECECEC"), ("selected", "#ECECEC")],
    )
    style.configure("TNotebook", background="#161616", borderwidth=0)
    style.configure(
        "TNotebook.Tab",
        background="#272727",
        foreground="#a9a9a9",
        font=(None, 14),
        borderwidth=1,
        relief="flat",
    )
    style.map(
        "TNotebook.Tab",
        background=[("active", "#383838"), ("selected", "#383838")],
        foreground=[("active", "#ECECEC"), ("selected", "#ECECEC")],
    )
    style.configure("TFrame", background="#161616", foreground="#ECECEC")
    style.configure(
        "TScrollbar",
        background="#272727",
        troughcolor="#383838",
        width=24,
        arrowsize=16,
        relief="flat",
        borderwidth=0,
        arrowcolor="#a9a9a9",
    )
    style.map("TScrollbar", background=[("active", "#272727")])
    style.layout(
        "Vertical.TScrollbar",
        [
            (
                "Vertical.Scrollbar.trough",
                {
                    "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})],
                    "sticky": "ns",
                },
            )
        ],
    )
    style.configure(
        "TCombobox", foreground="#000000", background="#555555", borderwidth=0, arrowsize=24
    )
    style.map(
        "TCombobox",
        background=[("active", "#666666"), ("selected", "#383838")],
        fieldbackground=[("readonly", "#A9A9A9"), ("disabled", "#999999")],
        borderwidth=[("active", 0)],
    )
    root.option_add("*TCombobox*Listbox*Font", (None, 18))
    root.option_add("*TCombobox*Listbox.foreground", "#000000")
    root.option_add("*TCombobox*Listbox.background", "#A9A9A9")
    root.option_add("*TCombobox*Listbox.selectForeground", "#ECECEC")
    root.option_add("*TCombobox*Listbox.selectBackground", "#272727")
