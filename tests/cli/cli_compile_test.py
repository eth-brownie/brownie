#!/usr/bin/python3

import pytest
import sys
import os
from pathlib import Path

from brownie import config, project
from brownie.cli.compile import main as compile_main


project_path = Path("tests/brownie-test-project")
sources = project.sources.Sources()
build = project.build.Build()


@pytest.fixture(autouse=True, scope="function")
def setup():
    argv = sys.argv
    sys.argv = ['brownie', 'compile']
    path = config['folders']['project']
    config['folders']['project'] = None
    original_path = os.getcwd()
    os.chdir(original_path+"/tests/brownie-test-project")
    source_data = sources._data
    sources._data = {}
    build_json = build._build
    build._build = {}
    yield
    sys.argv = argv
    sources._data = source_data
    build._build = build_json
    config['folders']['project'] = path
    os.chdir(original_path)


def test_compile_project():
    mtime = {}
    for i in ["SafeMath.json", "TokenABC.json", "TokenInterface.json", "Token.json"]:
        path = Path('build/contracts/'+i)
        assert path.exists()
        mtime[path] = path.stat().st_mtime
    compile_main()
    for k, v in mtime.items():
        assert k.stat().st_mtime == v, "recompiled unchanged contracts"


def test_compile_all():
    mtime = {}
    for i in ["SafeMath.json", "TokenABC.json", "TokenInterface.json", "Token.json"]:
        path = Path('build/contracts/'+i)
        assert path.exists()
        mtime[path] = path.stat().st_mtime
    sys.argv.append('--all')
    compile_main()
    for k, v in mtime.items():
        assert k.stat().st_mtime != v, "--all flag did not recompile entire project"


def test_compile_subdir():
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
