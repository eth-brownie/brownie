#!/usr/bin/python3

import os
from pathlib import Path
import pytest
import sys

from brownie.cli.__main__ import main as cli_main


@pytest.fixture(scope="module")
def project_path():
    original_path = os.getcwd()
    os.chdir(original_path+"/tests/brownie-test-project")
    yield Path(original_path+"/tests/brownie-test-project")
    os.chdir(original_path)


@pytest.fixture(scope="function")
def cli_tester(monkeypatch):
    c = CliTester(monkeypatch)
    yield c
    c.close()


class CliTester:

    def __init__(self, monkeypatch):
        self.argv = sys.argv.copy()
        self.monkeypatch = monkeypatch
        self.called = False
        self.total = 0
        self.count = 0

    def patch(self, location):
        self.monkeypatch.setattr(location, self.catch)

    def counter_patch(self, *locations):
        for item in locations:
            self.monkeypatch.setattr(item, self.simplecatch)
            self.total += 1

    def __call__(self, argv, *args, **kwargs):
        sys.argv = ['brownie']+argv.split(' ')
        self.args = args
        self.kwargs = kwargs
        cli_main()
        assert self.called is True
        assert self.count == self.total
        self.called = False
        self.count = 0

    def catch(self, *args, **kwargs):
        assert self.args == args
        assert self.kwargs == kwargs
        self.called = True

    def simplecatch(self, *args, **kwargs):
        self.count += 1

    def close(self):
        sys.argv = self.argv


def test_cli_init(cli_tester, noload):
    cli_tester.patch('brownie.project.new')
    cli_tester('init', '.', False)
    cli_tester('init test/path --force', 'test/path', True)


def test_cli_bake(cli_tester, noload):
    cli_tester.patch('brownie.project.pull')
    cli_tester('bake token', 'token', None, False)
    cli_tester('bake token test/path --force', 'token', 'test/path', True)


def test_cli_compile(cli_tester, project_path):
    cli_tester.patch('brownie.project.load')
    cli_tester('compile', project_path)
    cli_tester.counter_patch('shutil.rmtree')
    cli_tester('compile --all', project_path)


def test_cli_console(cli_tester, project_path):
    cli_tester.patch('brownie.cli.utils.console.Console.interact')
    cli_tester.counter_patch('brownie.project.load', 'brownie.network.connect')
    cli_tester('console', banner="Brownie environment is ready.", exitmsg="")


# travis doesn't like this

# def test_cli_gui(cli_tester, project_path):
#     cli_tester.patch('brownie.gui.Gui.mainloop')
#     cli_tester.counter_patch('brownie.project.load')
#     cli_tester('gui')


def test_cli_run(cli_tester, project_path):
    cli_tester.patch('brownie.test.main.run_script')
    cli_tester.counter_patch('brownie.project.load', 'brownie.network.connect')
    cli_tester('run testfile', 'testfile', 'main', gas_profile=False)
    cli_tester('run testfile xx --gas', 'testfile', 'xx', gas_profile=True)


def test_cli_test(cli_tester, project_path):
    cli_tester.patch('brownie.test.main.run_tests')
    cli_tester.counter_patch('brownie.project.load')
    cli_tester('test', None, False, False, False)
    cli_tester('test test/path --coverage --gas --update', 'test/path', True, True, True)
