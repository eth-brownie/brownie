#!/usr/bin/python3

import os
from pathlib import Path

import pytest

from brownie.project.scripts import run


def test_mix(plugintesterbase, project, tmp_path, chain, package_test):
    path = Path(project.from_brownie_mix("token", tmp_path.joinpath("testmix")))
    os.chdir(path)

    # tests should pass without fails or errors
    result = plugintesterbase.runpytest("-C")
    outcomes = result.parseoutcomes()
    assert "error" not in outcomes
    assert "failed" not in outcomes

    # scripts should execute
    mix_project = project.load(path)
    try:
        for script in path.glob("scripts/*.py"):
            run(str(script), "main", project=mix_project)
            chain.reset()
    finally:
        mix_project.close()


def test_from_brownie_mix_raises(project, tmp_path):
    project.new(tmp_path.joinpath("token"))
    with pytest.raises(FileExistsError):
        project.from_brownie_mix("token")
