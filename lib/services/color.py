#!/usr/bin/python3

import json
from pygments import highlight
from pygments.lexers import JsonLexer, PythonLexer
from pygments.formatters import TerminalFormatter


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

def color(name=None):
	if not name:
		return BASE+"m"
	name = name.split()
	if len(name) == 2:
		return BASE+MODIFIERS[name[0]]+COLORS[name[1]]+"m"
	return BASE+COLORS[name[0]]+"m"

def print_json(value):
	msg = json.dumps(value, default=str, indent=4, sort_keys=True)
	print(highlight(msg, JsonLexer(), TerminalFormatter()))

def print_python(*args):
	print(highliht(" ".join(args), PythonLexer(), TerminalFormatter()))