#!/usr/bin/python3

import os
import pytest

from brownie import config

# this isn't being used yet
@pytest.fixture
def cli(monkeypatch):
    path = config['folders']['project']
    config['folders']['project'] = None
    monkeypatch.setattr('brownie.project.load', lambda x: "")
    original_path = os.getcwd()
    os.chdir(original_path+"/tests/brownie-test-project")
    yield
    config['folders']['project'] = path
    os.chdir(original_path)


@pytest.fixture
def testpath(tmpdir):
    original_path = os.getcwd()
    os.chdir(tmpdir)
    yield tmpdir
    os.chdir(original_path)
