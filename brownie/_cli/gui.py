import click

from brownie import project
from brownie._gui import Gui


@click.command(short_help="Load the GUI to view opcodes and test coverage")
def cli():
    """
    Opens the brownie GUI. Basic functionality is as follows:
     * Selecting an opcode will highlight the associated source code.\n
     * Highlighting a section of the source will jump to the most relevent opcode,
       if possible.\n
     * Opcodes with a darkened background have no associated source code.\n
     * Type a pc number to jump to that opcode.\n
     * Right click an opcode to toggle highlighting on all opcodes of the same type.\n
     * Press J to toggle highlighting on JUMP, JUMPI and JUMPDEST opcodes.\n
     * Press R to toggle highlighting on all REVERT opcodes.\n
     * Select a section of source code and press S to enter scope mode. The
       instructions will be filtered to only display opcodes related to the relevent
       code. Press A to disable and see all opcodes again.\n
     * Press C to toggle unit test coverage visualization. This will only work if
       you have already run brownie coverage on your project. The coverage results
       are shown via different colors of text highlight.
    """
    project.load()
    print("Loading Brownie GUI...")
    Gui().mainloop()
    print("GUI was terminated.")
