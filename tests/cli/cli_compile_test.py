#!/usr/bin/python3

import pytest
import sys
import os
from pathlib import Path

from brownie import project
from brownie.cli.compile import main as compile_main


project_path = Path("tests/brownie-test-project")
sources = project.sources.Sources()
build = project.build.Build()


@pytest.fixture(autouse=True, scope="function")
def setup():
    argv = sys.argv
    sys.argv = ['brownie', 'compile']
    original_path = os.getcwd()
    os.chdir(original_path+"/tests/brownie-test-project")
    yield
    sys.argv = argv
    os.chdir(original_path)


def test_compile_project(noload):
    mtime = {}
    for i in ["SafeMath.json", "TokenABC.json", "TokenInterface.json", "Token.json"]:
        path = Path('build/contracts/'+i)
        assert path.exists()
        mtime[path] = path.stat().st_mtime
    compile_main()
    for k, v in mtime.items():
        assert k.stat().st_mtime == v, "recompiled unchanged contracts"


def test_compile_all(noload):
    mtime = {}
    for i in ["SafeMath.json", "TokenABC.json", "TokenInterface.json", "Token.json"]:
        path = Path('build/contracts/'+i)
        assert path.exists()
        mtime[path] = path.stat().st_mtime
    sys.argv.append('--all')
    compile_main()
    for k, v in mtime.items():
        assert k.stat().st_mtime != v, "--all flag did not recompile entire project"


def test_compile_subdir(noload):
    mtime = {}
    for i in ["SafeMath.json", "TokenABC.json", "TokenInterface.json", "Token.json"]:
        path = Path('build/contracts/'+i)
        mtime[path] = path.stat().st_mtime
    path = os.getcwd()
    os.chdir(path+"/contracts")
    compile_main()
    os.chdir(path)
    for k, v in mtime.items():
        assert k.stat().st_mtime == v, "compiling in subdirectory resulted in recompile"
