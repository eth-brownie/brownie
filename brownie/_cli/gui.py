#!/usr/bin/python3

from brownie import project
from brownie._gui import Gui
from brownie.utils.docopt import docopt

__doc__ = """Usage: brownie gui

Options:
  --help -h                  Display this message

Opens the brownie GUI. Basic functionality is as follows:

 * Selecting an opcode will highlight the associated source code.
 * Highlighting a section of the source will jump to the most relevent opcode,
   if possible.
 * Opcodes with a darkened background have no associated source code.
 * Type a pc number to jump to that opcode.
 * Right click an opcode to toggle highlighting on all opcodes of the same type.
 * Press J to toggle highlighting on JUMP, JUMPI and JUMPDEST opcodes.
 * Press R to toggle highlighting on all REVERT opcodes.
 * Select a section of source code and press S to enter scope mode. The
   instructions will be filtered to only display opcodes related to the relevent
   code. Press A to disable and see all opcodes again.
 * Press C to toggle unit test coverage visualization. This will only work if
   you have already run brownie coverage on your project. The coverage results
   are shown via different colors of text highlight."""


def main():
    docopt(__doc__)
    project.load()
    print("Loading Brownie GUI...")
    Gui().mainloop()
    print("GUI was terminated.")
