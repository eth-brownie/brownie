#!/usr/bin/python3

import os
import subprocess
from subprocess import DEVNULL

from brownie.services import config
CONFIG = config.CONFIG


def _run(cmd):
    path = os.path.abspath('.')
    os.chdir(CONFIG['folders']['brownie'])
    subprocess.run(cmd.split(), stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL)
    os.chdir(path)


def _output(cmd):
    path = os.path.abspath('.')
    os.chdir(CONFIG['folders']['brownie'])
    output = subprocess.check_output(cmd.split()).decode()
    os.chdir(path)
    return output


def get_commit():
    return _output('git log -n 1 --pretty=format:"%H"')[1:8]


def get_branch():
    return _output('git symbolic-ref HEAD').split('/')[-1][:-1]


def pull():
    version = get_commit()
    _run('git pull')
    if version == get_commit():
        return False
    _run('venv/bin/pip install -r requirements.txt')
    return True


def checkout(branch):
    _run('git fetch origin '+branch)
    _run('git checkout '+branch)
