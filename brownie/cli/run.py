#!/usr/bin/python3

from docopt import docopt
import importlib
from pathlib import Path
import sys


import brownie.network as network
from brownie.cli.utils import color
from brownie._config import ARGV, CONFIG



__doc__ = """Usage: brownie run <filename> [<function>] [options]

Arguments:
  <filename>           The name of the script to run
  [<function>]         The function to call (default is main)

Options:
  --network [name]     Use a specific network (default {})
  --verbose -v         Enable verbose reporting
  --tb -t              Show entire python traceback on exceptions
  --help -h            Display this message

Use run to execute scripts that deploy or interact with contracts on the network.
""".format(CONFIG['network_defaults']['name'])


def main():
    args = docopt(__doc__)
    ARGV._update_from_args(args)
    name = args['<filename>'].replace(".py", "")
    fn = args['<function>'] or "main"
    if not Path(CONFIG['folders']['project']).joinpath('scripts/{}.py'.format(name)):
        sys.exit("{0[error]}ERROR{0}: Cannot find {0[module]}scripts/{1}.py{0}".format(color, name))
    network.connect(ARGV['network'])
    module = importlib.import_module("scripts."+name)
    if not hasattr(module, fn):
        sys.exit("{0[error]}ERROR{0}: {0[module]}scripts/{1}.py{0} has no '{0[callable]}{2}{0}' function.".format(color, name, fn))
    print("Running '{0[module]}{1}{0}.{0[callable]}{2}{0}'...".format(color, name, fn))
    try:
        getattr(module, fn)()
        print("\n{0[success]}SUCCESS{0}: script '{0[module]}{1}{0}' completed.".format(color, name))
    except Exception as e:
        if CONFIG['logging']['exc'] >= 2:
            print("\n"+color.format_tb(sys.exc_info()))
        print("\n{0[error]}ERROR{0}: Script '{0[module]}{1}{0}' failed from unhandled {2}: {3}".format(
            color, name, type(e).__name__, e
        ))
