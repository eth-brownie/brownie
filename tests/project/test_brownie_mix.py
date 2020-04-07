#!/usr/bin/python3

import os
from pathlib import Path

import pytest

from brownie.project.scripts import run


# browniemix is parametrized with every mix repo from https://www.github.com/brownie-mix/
def test_mixes(plugintesterbase, project, tmp_path, rpc, browniemix, package_test):
    path = Path(project.from_brownie_mix(browniemix, tmp_path.joinpath("testmix")))
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
            rpc.reset()
    finally:
        mix_project.close()


def test_from_brownie_mix_raises(project, tmp_path):
    project.new(tmp_path.joinpath("token"))
    with pytest.raises(FileExistsError):
        project.from_brownie_mix("token")
    with pytest.raises(SystemError):
        project.from_brownie_mix(tmp_path.joinpath("token/contracts"))
