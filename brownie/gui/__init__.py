#!/usr/bin/python3

import sys
import os

from lib.root import Root
from lib.styles import set_style

if not os.path.exists("build/contracts"):
    sys.exit("ERROR: build/contracts folder is missing, is this a brownie project?")

root = Root()
set_style(root)
root.mainloop()