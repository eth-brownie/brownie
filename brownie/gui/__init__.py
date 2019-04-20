#!/usr/bin/python3

import sys
import os

from .root import Root
from .styles import set_style

root = Root()
set_style(root)
root.mainloop()