#!/usr/bin/python3

from docopt import docopt
import importlib
import os
import sys

from lib.components.network import Network
from lib.services import color
from lib.components import config
CONFIG = config.CONFIG


__doc__ = """Usage: brownie deploy <filename> [options]

Arguments:
  <filename>         The name of the deployment script to run

Options:
  --help             Display this message
  --network [name]   Use a specific network (default {})
  --verbose          Enable verbose reporting

Use deploy to run scripts intended to deploy contracts onto the network.
""".format(CONFIG['network_defaults']['name'])

def main():
    args = docopt(__doc__)
    name = args['<filename>'].replace(".py", "")
    if not os.path.exists("deployments/{}.py".format(name)):
        sys.exit("{0[bright red]}ERROR{0}: Cannot find {0[bright yellow]}deployments/{1}.py{0".format(color, name))

    module = importlib.import_module("deployments."+name)
    print("Running deployment script '{0[bright yellow]}{1}{0}'...".format(color, name))
    try:
        Network(module).run(name)
        print("\n{0[bright green]}SUCCESS{0}: Deployment script '{0[bright yellow]}{1}{0}' completed.".format(color, name))      
    except Exception as e:
        if CONFIG['logging']['exc']>=2:
            print("\n"+color.format_tb(sys.exc_info(), "deployments/"+name))
        print("\n{0[bright red]}ERROR{0}: Deployment of '{1}' failed from unhandled {2}: {3}".format(
            color, name, type(e).__name__, e
        ))