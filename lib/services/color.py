#!/usr/bin/python3

import json
from pygments import highlight
from pygments.lexers import JsonLexer, PythonLexer
from pygments.formatters import TerminalFormatter
import sys
import traceback

from lib.services import config
CONFIG = config.CONFIG

BASE = "\x1b[0;"

MODIFIERS = {
    'bright':"1;",
    'dark':"2;"
}

COLORS = {
    'black': "30",
    'red': "31",
    'green': "32",
    'yellow': "33",
    'blue': "34",
    'magenta': "35",
    'cyan': "36",
    'white': "37"
}

TB_BASE = (
    "  {0[dark white]}File {0[bright magenta]}{1[1]}{0[dark white]}, line "
    "{0[bright cyan]}{1[3]}{0[dark white]}, in {0[bright blue]}{1[5]}{0}{2}"
)




class Color:
    
    key = None
    value = None
    
    def set_colors(self, key, value):
        self.key = key
        self.value = value
    
    def __call__(self, color = None):
        if color in CONFIG['colors']:
            color = CONFIG['colors'][color]
        if not color:
            return BASE+"m"
        color = color.split()
        if len(color) == 2:
            return BASE+MODIFIERS[color[0]]+COLORS[color[1]]+"m"
        return BASE+COLORS[color[0]]+"m"

    def __str__(self):
        return BASE+"m"

    def __getitem__(self, color):
        return self(color)

    def json(self, value):
        msg = json.dumps(value, default=str, indent=4, sort_keys=True)
        print(highlight(msg, JsonLexer(), TerminalFormatter()))

    def print_colors(self, msg, key = None, value=None):
        if key is None:
            key = 'key'
        if value is None:
            value = 'value'
        for line in msg.split('\n'):
            if ':' not in line:
                print(line)
                continue
            line = line.split(':')
            line[0] = self(key) + line[0]
            line[-1] = self(value) + line[-1]
            for i in range(1,len(line)-1):
                line[i] = (
                    self(value) +
                    line[i][:line[i].index('  ')+1] +
                    self(key) +
                    line[i][line[i].index('  ')+1:]
                )
            line = ":".join(line)
        
            for s in ('(',')','/'):
                line = line.split(s)
                line = s.join([self(value)+i+self(key) for i in line])
            print(line+self())

    def format_tb(self, exc, filename = None, start = None, stop = None):
        tb = [i.replace("./", "") for i in traceback.format_tb(exc[2])]
        if filename:
            start = tb.index(next(i for i in tb if filename in i))
            stop = tb.index(next(i for i in tb[::-1] if filename in i)) + 1
        tb = tb[start:stop]
        for i in range(len(tb)):
            info, code = tb[i].split('\n')[:2]
            info = [x.strip(',') for x in info.strip().split(' ')]
            tb[i] = TB_BASE.format(self, info, "\n"+code if code else "")
        tb.append("{0[bright red]}{1}{0}: {2}".format(self, exc[0].__name__, exc[1]))
        return "\n".join(tb)


sys.modules[__name__] = Color()