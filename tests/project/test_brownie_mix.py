#!/usr/bin/python3

import os
from pathlib import Path
import pytest
import requests


from brownie.project.scripts import run

MIXES = [i['name'] for i in requests.get('https://api.github.com/orgs/brownie-mix/repos').json()]


@pytest.mark.parametrize('browniemix', MIXES)
def test_mix(plugintesterbase, project, tmp_path, rpc, browniemix):
    path = Path(project.pull(browniemix, tmp_path.joinpath('testmix')))
    os.chdir(path)

    # tests should pass without fails or errors
    result = plugintesterbase.runpytest('-C')
    outcomes = result.parseoutcomes()
    assert 'error' not in outcomes
    assert 'failed' not in outcomes

    # scripts should execute
    mix_project = project.load(path)
    try:
        for script in path.glob('scripts/*.py'):
            run(str(script), "main", project=mix_project)
            rpc.reset()
    finally:
        mix_project.close()
