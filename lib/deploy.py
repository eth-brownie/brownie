#!/usr/bin/python3

from docopt import docopt
import importlib
import os
import sys
import traceback

from lib.components.network import Network
from lib.components import config
CONFIG = config.CONFIG


__doc__ = """Usage: brownie [options] deploy <filename>

Arguments:
  <filename>         The name of the deployment script to run

Options:
  --help             Display this message
  --network [name]   Use a specific network (default {})
  --verbose          Enable verbose reporting

Use deploy to run scripts intended to deploy contracts onto the network.
""".format(CONFIG['default_network'])

def main():
    args = docopt(__doc__, options_first=True)
    name = args['<filename>'].replace(".py", "")
    if not os.path.exists("deployments/{}.py".format(name)):
        sys.exit("ERROR: Cannot find deployments/{}.py".format(name))

    module = importlib.import_module("deployments."+name)
    print("Running deployment script '{}'...".format(name))
    try:
        Network(module).run(name)
        print("\nDeployment script '{}' completed successfully.".format(name))      
    except Exception as e:
    if CONFIG['logging']['exc']>=2:
        print("".join(traceback.format_tb(sys.exc_info()[2])))
    print("ERROR: Deployment of '{}' failed from unhandled {}: {}".format(
        name, type(e).__name__, e
    ))