#!/usr/bin/python3

import json
from pygments import highlight
from pygments.lexers import JsonLexer, PythonLexer
from pygments.formatters import TerminalFormatter
import sys


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

class Color:
    
    key = None
    value = None

    def set_colors(self, key, value):
        self.key = key
        self.value = value
    
    def __call__(self, color = None):
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
            key = self.key
        if value is None:
            value = self.value
        for line in msg.split('\n'):
            if ':' not in line:
                print(line)
                continue
            line = line.split(':')
            line[0] = self(key)+line[0]
            line[-1] = self(value)+line[-1]
            for i in range(1,len(line)-1):
                line[i] = self(value)+line[i][:line[i].index('  ')+1]+self(key)+line[i][line[i].index('  ')+1:]
            line = ":".join(line)
        
            for s in ('(',')','/'):
                line = line.split(s)
                line = s.join([self(value)+i+self(key) for i in line])
            print(line+self())

sys.modules[__name__] = Color()