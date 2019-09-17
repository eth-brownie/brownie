#!/usr/bin/python3

import pytest
import sys

from brownie.cli.__main__ import main as cli_main


@pytest.fixture
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

    def set_target(self, target):
        self.monkeypatch.setattr(target, self.catch)

    def set_subtargets(self, *targets):
        for item in targets:
            self.monkeypatch.setattr(item, self.incremental_catch)
            self.total += 1

    def run(self, argv, args=(), kwargs={}):
        sys.argv = ["brownie"] + argv.split(" ")
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

    def incremental_catch(self, *args, **kwargs):
        self.count += 1

    def close(self):
        sys.argv = self.argv


def test_cli_init(cli_tester):
    cli_tester.set_target("brownie.project.new")
    cli_tester.run("init", args=(".", False))
    cli_tester.run("init test/path --force", args=("test/path", True))


def test_cli_bake(cli_tester):
    cli_tester.set_target("brownie.project.pull")
    cli_tester.run("bake token", args=("token", None, False))
    cli_tester.run("bake token test/path --force", args=("token", "test/path", True))


def test_cli_compile(cli_tester, testproject):
    cli_tester.set_target("brownie.project.load")
    cli_tester.run("compile", args=(testproject._project_path,))
    cli_tester.run("compile --all", args=(testproject._project_path,))


def test_cli_console(cli_tester, testproject):
    testproject.close()
    cli_tester.set_target("brownie.cli.console.Console.interact")
    cli_tester.set_subtargets("brownie.network.connect")
    cli_tester.run(
        "console", kwargs={"banner": "Brownie environment is ready.", "exitmsg": ""}
    )


# travis doesn't like this

# def test_cli_gui(cli_tester, project_path):
#     cli_tester.patch('brownie.gui.Gui.mainloop')
#     cli_tester.counter_patch('brownie.project.load')
#     cli_tester('gui')


def test_cli_run(cli_tester, project):
    cli_tester.set_target("brownie.run")
    cli_tester.set_subtargets("brownie.network.connect")
    cli_tester.run(
        "run testfile",
        args=("testfile",),
        kwargs={"method_name": "main", "project": None},
    )
    cli_tester.run(
        "run testfile xx --gas",
        args=("testfile",),
        kwargs={"method_name": "xx", "project": None},
    )


def test_cli_incorrect(cli_tester):
    with pytest.raises(SystemExit):
        cli_tester.run("foo")
