#!/usr/bin/python3

import importlib
import os
import sys
import traceback


if "--help" in sys.argv or len(sys.argv)<3 or sys.argv[2][:2]=="--":
    sys.exit("""Usage: brownie deploy <filename> [options]

Arguments:
  <filename>         The name of the deployment script to run

Use deploy to run scripts intended to deploy contracts onto the network.""")


from lib.components import config
CONFIG = config.CONFIG

name = sys.argv[2].replace(".py","")
if not os.path.exists(CONFIG['folders']['project']+'/deployments/{}.py'.format(name)):
    sys.exit("ERROR: Cannot find deployments/{}.py".format(name))

from lib.components.network import Network

module = importlib.import_module("deployments."+name)
print("Running deployment script '{}'...".format(name))
try:
    Network(module).run(name)
    print("\nSUCCESS: deployment script '{}' completed successfully.".format(name))      
except Exception as e:
   if CONFIG['logging']['exc']>=2:
       print("".join(traceback.format_tb(sys.exc_info()[2])))
   print("ERROR: Deployment of '{}' failed from unhandled {}: {}".format(
       name, type(e).__name__, e))