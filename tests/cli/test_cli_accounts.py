#!/usr/bin/python3

import json

import pytest

from brownie._cli import accounts as cli_accounts
from brownie._config import _get_data_folder


@pytest.fixture(autouse=True)
def no_pass(monkeypatch):
    monkeypatch.setattr("brownie.network.account.getpass", lambda x: "")


def test_new_account(capfd, monkeypatch):
    assert not _get_data_folder().joinpath("accounts/new.json").exists()
    cli_accounts._list()
    assert "0x3b9b63C67838C9fef6c50e3a06f574Be12b3D50f" not in capfd.readouterr()[0]
    monkeypatch.setattr(
        "builtins.input",
        lambda x: "0x60285766d7296d0744450696603d9593513958fdbb494cc6d234a5a797a2108f",
    )
    cli_accounts._new("new")
    capfd.readouterr()
    cli_accounts._list()
    assert "0x3b9b63C67838C9fef6c50e3a06f574Be12b3D50f" in capfd.readouterr()[0]
    assert _get_data_folder().joinpath("accounts/new.json").exists()


def test_generate(capfd):
    path = _get_data_folder().joinpath("accounts/generate.json")
    assert not path.exists()
    cli_accounts._generate("generate")
    assert path.exists()
    with path.open() as fp:
        data = json.load(fp)
    capfd.readouterr()
    cli_accounts._list()
    assert data["address"] in capfd.readouterr()[0].lower()


def test_import():
    path = _get_data_folder().joinpath("accounts/import-test.json")
    cli_accounts._generate("import-test")
    new_path = _get_data_folder().joinpath("x.json")
    path.rename(new_path)
    cli_accounts._import("import-new", str(new_path.absolute()))
    assert _get_data_folder().joinpath("accounts/import-new.json").exists()


def test_import_already_exists():
    cli_accounts._generate("import-exists")
    with pytest.raises(FileExistsError):
        cli_accounts._import("import-exists", "")


def test_export():
    cli_accounts._generate("export-test")
    target_path = _get_data_folder().joinpath("exported.json")
    assert not target_path.exists()
    cli_accounts._export("export-test", str(target_path.absolute()))
    assert target_path.exists()


def test_export_not_exists():
    with pytest.raises(FileNotFoundError):
        cli_accounts._export("unknown", "")


def test_export_overwrite():
    cli_accounts._generate("export-exists")
    path = str(_get_data_folder().joinpath("accounts/export-exists.json").absolute())
    with pytest.raises(FileExistsError):
        cli_accounts._export("export-exists", path)


def test_password(monkeypatch, accounts):
    cli_accounts._generate("pw-test")
    passwords = ["xxx", "xxx", ""]
    monkeypatch.setattr("brownie.network.account.getpass", lambda x: passwords.pop())
    cli_accounts._password("pw-test")
    accounts.load("pw-test")


def test_delete():
    cli_accounts._generate("del-test")
    path = _get_data_folder().joinpath("accounts/del-test.json")
    assert path.exists()
    cli_accounts._delete("del-test")
    assert not path.exists()
