#!/usr/bin/python3

from pathlib import Path
from subprocess import run, DEVNULL


def test_init_project(tmpdir):
    _run(tmpdir)
    project_path = Path(tmpdir)
    for path in ("contracts", "scripts", "reports", "tests", "brownie-config.json"):
        assert project_path.joinpath(path).exists()


def test_init_inside(tmpdir):
    _run(tmpdir)
    _run(tmpdir+"/contracts")
    project_path = Path(tmpdir)
    assert not project_path.joinpath(tmpdir+"/contracts/brownie-config.json").exists()


def _run(cwd):
    run(['brownie', 'init'], cwd=cwd, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, check=True)
