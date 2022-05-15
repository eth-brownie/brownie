#!/usr/bin/python3

import re
import tkinter as tk
import tkinter.font as tkFont
from pathlib import Path
from tkinter import ttk

from brownie.project.sources import is_inside_offset

from .bases import SelectBox
from .styles import TEXT_COLORS, TEXT_STYLE


class SourceNoteBook(ttk.Notebook):
    def __init__(self, parent):
        super().__init__(parent)
        self.root = self._root()
        self._scope = None
        self.configure(padding=0)
        self._frames = []
        self.bind_count = 0
        self.root.bind("<Left>", self.key_left)
        self.root.bind("<Right>", self.key_right)
        base_path = self.root.active_project._path.joinpath(
            self.root.active_project._structure["contracts"]
        )
        for path in base_path.glob("**/*"):
            if path.suffix in (".sol", ".vy"):
                self.add(path)
        self.set_visible([])
        self.bind("<<NotebookTabChanged>>", self.on_tab_change)

    def add(self, path):
        path = Path(path)
        label = path.name
        if label in [i._label for i in self._frames]:
            return
        with path.open() as fp:
            frame = SourceFrame(self, fp.read(), path.suffix)
        super().add(frame, text=f"   {label}   ")
        frame._id = len(self._frames)
        frame._label = label
        frame._visible = True
        frame._path = str(path)
        self._frames.append(frame)

    def get_frame(self, label):
        label = Path(label).name
        return next(i for i in self._frames if i._label == label)

    def hide(self, label):
        frame = self.get_frame(label)
        if frame._visible:
            super().hide(frame)
            frame._visible = False

    def show(self, label):
        label = Path(label).name
        frame = next(i for i in self._frames if i._label == label)
        if frame._visible:
            return
        frame._visible = True
        super().add(frame, text=f"   {label}   ")

    def on_tab_change(self, event):
        if self.select():
            tab = event.widget.tab("current")["text"]
            self.root.toolbar.report.set_values(Path(tab).stem.strip())

    def set_visible(self, labels):
        labels = [Path(i).name for i in labels]
        for label in [i._label for i in self._frames]:
            if label in labels:
                self.show(label)
            else:
                self.hide(label)

    def active_frame(self):
        id_ = self.index(self.select())
        return self._frames[id_]

    def set_active(self, label):
        self.select(self.get_frame(label))

    def key_left(self, event):
        self._key([i for i in self._frames if i._visible][::-1])

    def key_right(self, event):
        self._key([i for i in self._frames if i._visible])

    def _key(self, visible):
        if not visible:
            return
        f = self.active_frame()
        if visible[-1] == f:
            self.select(visible[0])
        else:
            self.select(visible[visible.index(f) + 1])

    def apply_scope(self, start, stop):
        self.clear_scope()
        frame = self.active_frame()
        self._scope = [frame, start, stop]
        frame.tag_add("dark", 0, start)
        frame.tag_add("dark", stop, "end")
        for f in [v for v in self._frames if v != frame]:
            f.tag_add("dark", 0, "end")

    def clear_scope(self):
        self.unmark_all("dark")
        self._scope = None

    def show_msg(self, frame, tag, msg):
        text = self.root.main.console.read()
        frame.tag_bind(tag, "<Leave>", lambda e: self.root.main.console.write(text))
        self.root.main.console.write(msg)

    def mark(self, label, tag, start, stop, msg=None):
        frame = self.get_frame(label)
        frame.tag_add(tag, start, stop)
        self.root.main.console.read()
        if msg:
            bind_tag = f"bind-{self.bind_count}"
            frame.tag_add(bind_tag, start, stop)
            frame.tag_bind(bind_tag, "<Enter>", lambda e: self.show_msg(frame, bind_tag, msg))
            self.bind_count += 1

    def unmark(self, label, tag):
        frame = self.get_frame(label)
        frame.tag_remove(tag)

    def unmark_all(self, *tags):
        for frame in self._frames:
            for tag in tags:
                frame.tag_remove(tag)

    def unbind_all(self):
        for frame in self._frames:
            for tag in (f"bind-{i}" for i in range(self.bind_count)):
                frame.tag_remove(tag)
                frame.tag_unbind(tag, "<Enter>")
                frame.tag_unbind(tag, "<Leave>")
        self.bind_count = 0

    def _search(self, event):
        frame = self.active_frame()
        tree = self.root.main.oplist
        if not frame.tag_ranges("sel"):
            tree.clear_selection()
            return
        start, stop = frame.tag_ranges("sel")
        if self._scope and (
            frame != self._scope[0] or start < self._scope[1] or stop > self._scope[2]
        ):
            pc = False
        else:
            pc = [
                k
                for k, v in self.root.pcMap.items()
                if "path" in v
                and frame._label in self.root.pathMap[v["path"]]
                and is_inside_offset((start, stop), v["offset"])
            ]
        if not pc:
            frame.clear_highlight()
            tree.clear_selection()
            return

        def key(k):
            return (start - self.root.pcMap[k]["offset"][0]) + (
                self.root.pcMap[k]["offset"][1] - stop
            )

        id_ = sorted(pc, key=key)[0]
        tree.selection_set(id_)


class SourceFrame(tk.Frame):
    def __init__(self, root, text, suffix):
        super().__init__(root)
        self._text = tk.Text(self, width=90, yscrollcommand=self._text_scroll)
        self._scroll = ttk.Scrollbar(self)
        self._scroll.pack(side="left", fill="y")
        self._scroll.config(command=self._scrollbar_scroll)
        self._line_no = tk.Text(self, width=4, yscrollcommand=self._text_scroll)
        self._line_no.pack(side="left", fill="y")

        self._text.pack(side="right", fill="y")
        self._text.insert(1.0, text)

        for k, v in TEXT_COLORS.items():
            self._text.tag_config(k, **v)

        if suffix == ".sol":
            pattern = r"((?:\s*\/\/[^\n]*)|(?:\/\*[\s\S]*?\*\/))"
        else:
            pattern = r"((#[^\n]*\n)|(\"\"\"[\s\S]*?\"\"\")|('''[\s\S]*?'''))"
        for match in re.finditer(pattern, text):
            self.tag_add("comment", match.start(), match.end())

        self._line_no.insert(1.0, "\n".join(str(i) for i in range(1, text.count("\n") + 2)))
        self._line_no.tag_configure("justify", justify="right")
        self._line_no.tag_add("justify", 1.0, "end")

        for text in (self._line_no, self._text):
            text.config(**TEXT_STYLE)
            text.config(tabs=tkFont.Font(font=text["font"]).measure("    "), wrap="none")
        self._line_no.config(background="#272727")
        self._text.bind("<ButtonRelease-1>", root._search)

    def __getattr__(self, attr):
        return getattr(self._text, attr)

    def config(self, **kwargs):
        self._text.config(**kwargs)
        self._line_no.config(**kwargs)

    def clear_highlight(self):
        self._text.tag_remove("sel", 1.0, "end")

    def highlight(self, start, end):
        self.clear_highlight()
        self.tag_add("sel", start, end, True)

    def tag_add(self, tag, start, end, see=False):
        start = self._offset_to_coord(start)
        if type(end) is not str:
            end = self._offset_to_coord(end)
        self._text.tag_add(tag, start, end)
        if see:
            self._text.see(end)
            self._text.see(start)

    def tag_ranges(self, tag):
        return [self._coord_to_offset(i.string) for i in self._text.tag_ranges(tag)]

    def tag_remove(self, tag):
        self._text.tag_remove(tag, 1.0, "end")

    def _offset_to_coord(self, value):
        text = self._text.get(1.0, "end")
        line = text[:value].count("\n") + 1
        offset = len(text[:value].split("\n")[-1])
        return f"{line}.{offset}"

    def _coord_to_offset(self, value):
        row, col = [int(i) for i in value.split(".")]
        text = self._text.get(1.0, "end").split("\n")
        return sum(len(i) + 1 for i in text[: row - 1]) + col

    def _scrollbar_scroll(self, action, position, type=None):
        self._text.yview_moveto(position)
        self._line_no.yview_moveto(position)

    def _text_scroll(self, first, last, type=None):
        self._text.yview_moveto(first)
        self._line_no.yview_moveto(first)
        self._scroll.set(first, last)


class ContractSelect(SelectBox):
    def __init__(self, parent, values):
        super().__init__(parent, "Select a Contract", values)

    def _select(self, event):
        contract_name = super()._select()
        self.root.set_active_contract(contract_name)
