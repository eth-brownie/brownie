#!/usr/bin/python3

import json
from pathlib import Path
import pytest

from brownie.test import pathutils


# untested methods: get_ast_hash

@pytest.fixture()
def testpath():
    yield Path('tests/brownie-test-project/tests/brownie_tester/donothing.py').absolute()


@pytest.fixture(scope="function")
def buildpath():
    path = Path('tests/brownie-test-project/build/tests/brownie_tester/donothing.json').absolute()
    path.parent.mkdir(exist_ok=True)
    yield path
    if path.exists():
        path.unlink()


def test_check_build_hashes(testpath, buildpath):
    pathutils.save_build_json(testpath, "potato", {'result': "potatoes"}, ["Token"])
    assert buildpath.exists()
    pathutils.check_build_hashes("tests/brownie-test-project")
    assert buildpath.exists()
    build_json = json.load(buildpath.open())
    build_json['sha1']["build/contracts/Token.json"] = "potato"
    json.dump(build_json, buildpath.open('w'))
    pathutils.check_build_hashes("tests/brownie-test-project")
    assert not buildpath.exists()


def test_remove_empty_folders(tmpdir):
    a = Path(tmpdir).joinpath('test')
    a.mkdir()
    b = Path(tmpdir).joinpath('test2')
    b.mkdir()
    b.joinpath('tempfile').touch()
    pathutils.remove_empty_folders(tmpdir)
    assert not a.exists()
    assert b.exists()


def test_get_paths(testpath):
    assert testpath in pathutils.get_paths('tests/brownie-test-project/tests')
    assert testpath not in pathutils.get_paths('tests/brownie-test-project/tests/token')
    assert testpath in pathutils.get_paths()
    assert [testpath] == pathutils.get_paths(str(testpath))
    with pytest.raises(FileNotFoundError):
        pathutils.get_paths('potato')


def test_get_build_paths(testpath, buildpath):
    assert [buildpath] == pathutils.get_build_paths([testpath])


def test_get_build_json(testpath, buildpath):

    assert pathutils.get_build_json(testpath) == {'result': None, 'coverage': {}, 'sha1': {}}
    assert buildpath.parent.exists()
    buildpath.open('w').write('potato')
    assert pathutils.get_build_json(testpath) == {'result': None, 'coverage': {}, 'sha1': {}}
    assert not buildpath.exists()
    buildpath.open('w').write('{"result": 123}')
    assert pathutils.get_build_json(testpath) == {'result': 123}


def test_save_build_json(testpath, buildpath):
    pathutils.save_build_json(testpath, "potato", {'result': "potatoes"}, ["Token"])
    assert buildpath.exists()
    build_json = json.load(buildpath.open())
    assert build_json['result'] == "potato"
    assert build_json['coverage'] == {'result': "potatoes"}
    assert "build/contracts/Token.json" in build_json['sha1']


def test_save_report():
    path = pathutils.save_report({}, "tests/brownie-test-project/reports")
    assert path.exists()
    assert path.name.startswith('coverage')
    assert path != pathutils.save_report({}, "tests/brownie-test-project/reports")
    path = pathutils.save_report({}, "tests/brownie-test-project/reports/potato-report.json")
    assert path.name == "potato-report.json"
