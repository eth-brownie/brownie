#!/usr/bin/python3

from pathlib import Path
import re
import tkinter as tk
import tkinter.font as tkFont
from tkinter import ttk

from .styles import TEXT_STYLE, TEXT_COLORS

import brownie._config as config
CONFIG = config.CONFIG

class TextBook(ttk.Notebook):

    def __init__(self, root):
        super().__init__(root)
        self._parent = root
        self._scope = None
        self.configure(padding=0)
        self._frames = []
        root.bind("<Left>", self.key_left)
        root.bind("<Right>", self.key_right)
        base_path = Path(CONFIG['folders']['project']).joinpath('contracts')
        for path in base_path.glob('**/*.sol'):
            self.add(path)

    def add(self, path):
        label = path.name
        if label in [i._label for i in self._frames]:
            return
        frame = TextBox(self, path.open().read())
        super().add(frame, text="   {}   ".format(label))
        frame._id = len(self._frames)
        frame._label = label
        frame._visible = True
        frame._path = str(path)
        self._frames.append(frame)

    def get_frame(self, label):
        return next(i for i in self._frames if i._label == label)
    
    def hide(self, label):
        frame = self.get_frame(label)
        if frame._visible:
            super().hide(frame)
            frame._visible = False
    
    def show(self, label):
        frame = next(i for i in self._frames if i._label == label)
        if frame._visible:
            return
        frame._visible = True
        super().add(frame, text="   {}   ".format(label))

    def set_visible(self, labels):
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
        if visible[-1]  == f:
            self.select(visible[0])
        else:
            self.select(visible[visible.index(f)+1])

    def apply_scope(self, start, stop):
        self.clear_scope()
        frame = self.active_frame()
        self._scope = [frame, start, stop]
        frame.tag_add('dark', 0, start)
        frame.tag_add('dark', stop, 'end')
        for f in [v for v in self._frames if v!=frame]:
            f.tag_add('dark', 0, 'end')

    def clear_scope(self):
        self.unmark_all('dark')
        self._scope = None

    def mark(self, label, tag, start, stop):
        frame = self.get_frame(label)
        frame.tag_add(tag, start, stop)

    def unmark(self, label, tag):
        frame = self.get_frame(label)
        frame.tag_remove(tag)

    def unmark_all(self, *tags):
        for f in self._frames:
            for tag in tags:
                f.tag_remove(tag)
    
    def _search(self, event):
        frame = self.active_frame()
        tree = self._parent.tree
        if not frame.tag_ranges('sel'):
            tree.clear_selection()
            return
        start, stop = frame.tag_ranges('sel')
        if self._scope and (
            frame != self._scope[0] or
            start<self._scope[1] or
            stop>self._scope[2]
        ):
            pc = False
        else:
            pc = [
                k for k,v in self._parent.pcMap.items() if 
                v['contract'] and frame._label in v['contract'] and
                start >= v['start'] and stop <= v['stop']
            ]
        if not pc:
            frame.clear_highlight()
            tree.clear_selection()
            return
        def key(k):
            return (
                (start - self._parent.pcMap[k]['start']) + 
                (self._parent.pcMap[k]['stop'] - stop)
            )
        id_ = sorted(pc, key=key)[0]
        tree.selection_set(id_)


class TextBox(tk.Frame):

    def __init__(self, root, text):
        super().__init__(root)
        self._text = tk.Text(
            self,
            height = 35,
            width = 90,
            yscrollcommand = self._text_scroll
        )
        self._scroll = ttk.Scrollbar(self)
        self._scroll.pack(side="left", fill="y")
        self._scroll.config(command=self._scrollbar_scroll)
        self._line_no = tk.Text(
            self,
            height = 35,
            width = 4,
            yscrollcommand = self._text_scroll
        )
        self._line_no.pack(side="left", fill="y")

        self._text.pack(side="right",fill="y")
        self._text.insert(1.0, text)

        for k,v in TEXT_COLORS.items():
            self._text.tag_config(k, **v)

        for pattern in ('\/\*[\s\S]*?\*\/', '\/\/[^\n]*'):
            for i in re.findall(pattern, text):
                idx = text.index(i)
                self.tag_add('comment',idx,idx+len(i))

        self._line_no.insert(1.0, '\n'.join(str(i) for i in range(1, text.count('\n')+2)))
        self._line_no.tag_configure("justify", justify="right")
        self._line_no.tag_add("justify", 1.0, "end")

        for text in (self._line_no, self._text):
            text['state'] = "disabled"
            text.config(**TEXT_STYLE)
            text.config(
                tabs = tkFont.Font(font=text['font']).measure('    '),
                wrap = "none"
            )
        self._text.bind('<ButtonRelease-1>', root._search)

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
        line = text[:value].count('\n') + 1
        offset = len(text[:value].split('\n')[-1])
        return "{}.{}".format(line, offset)

    def _coord_to_offset(self, value):
        row, col = [int(i) for i in value.split('.')]
        text = self._text.get(1.0, "end").split('\n')
        return sum(len(i)+1 for i in text[:row-1])+col

    def _scrollbar_scroll(self, action, position, type=None):
        self._text.yview_moveto(position)
        self._line_no.yview_moveto(position)

    def _text_scroll(self, first, last, type=None):
        self._text.yview_moveto(first)
        self._line_no.yview_moveto(first)
        self._scroll.set(first, last)