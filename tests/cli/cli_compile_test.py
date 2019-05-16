#!/usr/bin/python3

from pathlib import Path
from subprocess import run, DEVNULL


project_path = Path("tests/brownie-test-project")


def test_compile_project():
    mtime = {}
    for i in ["SafeMath.json", "TokenABC.json", "TokenInterface.json", "Token.json"]:
        path = project_path.joinpath('build/contracts/'+i)
        mtime[path] = path.stat().st_mtime
    _run()
    for k, v in mtime.items():
        assert k.stat().st_mtime == v, "recompiled unchanged contracts"


def test_compile_all():
    mtime = {}
    for i in ["SafeMath.json", "TokenABC.json", "TokenInterface.json", "Token.json"]:
        path = project_path.joinpath('build/contracts/'+i)
        mtime[path] = path.stat().st_mtime
    _run(cmd=['--all'])
    for k, v in mtime.items():
        assert k.stat().st_mtime != v, "--all flag did not recompile entire project"


def test_compile_subdir():
    mtime = {}
    for i in ["SafeMath.json", "TokenABC.json", "TokenInterface.json", "Token.json"]:
        path = project_path.joinpath('build/contracts/'+i)
        mtime[path] = path.stat().st_mtime
    _run(cwd="/contracts")
    for k, v in mtime.items():
        assert k.stat().st_mtime == v, "compiling in subdirectory resulted in recompile"


def _run(cmd=[], cwd=""):
    run(
        ['brownie', 'compile']+cmd,
        cwd=str(project_path)+cwd,
        stdin=DEVNULL,
        stdout=DEVNULL,
        stderr=DEVNULL,
        check=True
    )
