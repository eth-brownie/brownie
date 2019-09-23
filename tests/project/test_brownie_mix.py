#!/usr/bin/python3

import os
import time
from base64 import b64encode
from pathlib import Path

import pytest
import requests

from brownie.project.scripts import run

if os.getenv("GITHUB_TOKEN"):
    auth = b64encode(os.getenv("GITHUB_TOKEN").encode()).decode()
    headers = {"Authorization": "Basic {}".format(auth)}
else:
    headers = None

for i in range(10):
    data = requests.get("https://api.github.com/orgs/brownie-mix/repos", headers=headers)
    if data.status_code == 200:
        break
    time.sleep(30)

if data.status_code != 200:
    raise ConnectionError("Cannot connect to Github API")

MIXES = [i["name"] for i in data.json()]


@pytest.mark.parametrize("browniemix", MIXES)
def test_mix(plugintesterbase, project, tmp_path, rpc, browniemix):
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
