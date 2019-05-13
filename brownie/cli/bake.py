#!/usr/bin/python3

from docopt import docopt
from io import BytesIO
from pathlib import Path
import requests
import shutil
import sys
import zipfile

from brownie._config import CONFIG

MIXES_URL = "https://github.com/brownie-mix/{}-mix/archive/master.zip"

__doc__ = """Usage: brownie bake <mix> [<path>] [options]

Arguments:
  <mix>                 Name of Brownie mix to initialize
  <path>                Path to initialize to (default is name of mix)

Options:
  --force -f            Allow init inside a project subfolder
  --help -h             Display this message

Brownie mixes are ready-made templates that you can use as a starting
point for your own project, or as a part of a tutorial.

For a complete list of Brownie mixes visit https://www.github.com/brownie-mixes
"""


def main():
    args = docopt(__doc__)
    path = Path(args['<path>'] or '.').resolve()
    final_path = path.joinpath(args['<mix>'])
    if final_path.exists():
        sys.exit("ERROR: Bake folder already exists - {}".format(final_path))

    if CONFIG['folders']['brownie'] in str(path):
        sys.exit(
            "ERROR: Cannot bake inside the main brownie installation folder.\n"
            "Create a new folder for your project and run brownie bake there."
        )

    print("Downloading from "+MIXES_URL.format(args['<mix>'])+" ...")
    request = requests.get(MIXES_URL.format(args['<mix>']))
    with zipfile.ZipFile(BytesIO(request.content)) as zf:
        zf.extractall(str(path))
    path.joinpath(args['<mix>']+'-mix-master').rename(final_path)
    shutil.copy(
        str(Path(CONFIG['folders']['brownie']).joinpath("data/config.json")),
        str(final_path.joinpath('brownie-config.json'))
    )

    print("Brownie mix '{}' has been initiated at {}".format(args['<mix>'], final_path))
    sys.exit()
