#!/usr/bin/python3

from docopt import docopt
from io import BytesIO
from pathlib import Path
import sys
imoprt tarfile

import brownie.config as config
CONFIG = config.CONFIG

MIXES_URL = "" # TODO

__doc__ = """Usage: brownie bake <mix> [<path>] [options]

Arguments:
  <mix>               Name of Brownie mix to initialize
  <path>              Path to initialize to (default is name of mix)

Options:
  --force             Allow init inside a project subfolder
  --help              Display this message

Brownie mixes are ready-made templates that you can use as a starting
point for your own project, or as a part of a tutorial.

For a complete list of Brownie mixes visit https://www.github.com/brownie-mixes
"""


def main():
    args = docopt(__doc__)
    path = Path(args['<path>'] or args['<mix>']).resolve()

    if CONFIG['folders']['brownie'] in str(path):
        sys.exit(
            "ERROR: Cannot bake inside the main brownie installation folder.\n"
            "Create a new folder for your project and run brownie bake there."
        )

    path.mkdir(exist_ok=True)
    request = requests.get(MIXES_URL+"") # TODO
    tarfile.open(BytesIO(request.content)) as tar:
        tar.extractall(str(path))

    print("Brownie mix '{}' has been initiated at {}".format(args['<mix>'], path))
    sys.exit()