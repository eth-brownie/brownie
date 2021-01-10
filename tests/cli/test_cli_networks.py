import pytest
import yaml

from brownie._cli import networks as cli_networks
from brownie._config import _get_data_folder


@pytest.fixture(autouse=True)
def isolation():
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    yield
    with _get_data_folder().joinpath("network-config.yaml").open("w") as fp:
        networks = yaml.dump(networks, fp)


def test_list(config, runner):
    result = runner.invoke(cli_networks.list)

    assert "chainid" not in result.output
    for key in config.networks:
        assert key in result.output


def test_list_verbose(config, runner):
    result = runner.invoke(cli_networks.list, ["--verbose"])

    assert "chainid" in result.output
    for key in config.networks:
        assert key in result.output


def test_add(runner):
    runner.invoke(cli_networks.add, ["ethereum", "tester", "host=127.0.0.1", "chainid=42"])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    assert networks["live"][0]["networks"][-1] == {
        "id": "tester",
        "host": "127.0.0.1",
        "chainid": 42,
        "name": "tester",
    }


def test_add_new_env(runner):
    runner.invoke(cli_networks.add, ["FooChain", "tester", "host=127.0.0.1", "chainid=42"])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    assert networks["live"][-1] == {
        "name": "FooChain",
        "networks": [{"id": "tester", "host": "127.0.0.1", "chainid": 42, "name": "tester"}],
    }


def test_add_exists(runner):
    result = runner.invoke(cli_networks.add,["FooChain", "development", "host=127.0.0.1", "chainid=42"])
    assert isinstance(result.exception, ValueError) is True


def test_add_missing_field(runner):
    result = runner.invoke(cli_networks.add, ["FooChain", "tester", "chainid=42"])
    assert isinstance(result.exception, ValueError) is True


def test_add_unknown_field(runner):
    result = runner.invoke(cli_networks.add, ["FooChain", "tester", "host=127.0.0.1", "chainid=42", "foo=bar"])
    assert isinstance(result.exception, ValueError) is True


def test_add_dev(runner):
    runner.invoke(cli_networks.add, ["development", "tester", "host=127.0.0.1", "cmd=foo", "port=411"])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    assert networks["development"][-1] == {
        "id": "tester",
        "host": "127.0.0.1",
        "cmd": "foo",
        "name": "tester",
        "cmd_settings": {"port": 411},
    }


def test_add_dev_missing_field(runner):
    result = runner.invoke(cli_networks.add, ["development", "tester", "host=127.0.0.1" "port=411"])
    assert isinstance(result.exception, ValueError) is True


def test_add_dev_unknown_field(runner):
    result = runner.invoke(cli_networks.add, ["development", "tester", "cmd=foo", "host=127.0.0.1" "chainid=411"])
    assert isinstance(result.exception, ValueError) is True


def test_modify(runner):
    runner.invoke(cli_networks.modify, ["mainnet", "chainid=3"])
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert networks["live"][0]["networks"][0]["chainid"] == 3


def test_modify_id(runner):
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        mainnet = yaml.safe_load(fp)["live"][0]["networks"][0]

    runner.invoke(cli_networks.modify, ["mainnet", "id=foo"])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        foo = yaml.safe_load(fp)["live"][0]["networks"][0]

    mainnet["id"] = "foo"
    assert mainnet == foo


def test_modify_remove(runner):
    runner.invoke(cli_networks.modify, ["development", "port=None"])
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert "port" not in networks["development"][0]["cmd_settings"]


def test_modify_add(runner):
    runner.invoke(cli_networks.modify, ["development", "fork=true"])
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert "fork" in networks["development"][0]["cmd_settings"]


def test_modify_unknown(runner):
    result = runner.invoke(cli_networks.modify, ["development", "foo=true"])
    assert isinstance(result.exception, ValueError) is True


def test_modify_remove_required(runner):
    result = runner.invoke(cli_networks.modify, ["development", "id=None"])
    assert isinstance(result.exception, ValueError) is True


def test_delete_live(runner):
    runner.invoke(cli_networks.delete, ["mainnet"])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert "mainnet" not in [i["id"] for i in networks["live"][0]["networks"]]


def test_delete_development(runner):
    runner.invoke(cli_networks.delete, ["development"])
    runner.invoke(cli_networks.delete, ["mainnet-fork"])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert not networks["development"]


def test_delete_all_networks_in_prod_environment(runner):
    runner.invoke(cli_networks.delete, ["etc"])
    runner.invoke(cli_networks.delete, ["kotti"])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert len(networks["live"]) == 1


def test_export(tmp_path, runner):
    path = tmp_path.joinpath("exported.yaml")
    runner.invoke(cli_networks.export, [path.as_posix()])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    with path.open() as fp:
        exported = yaml.safe_load(fp)

    assert networks == exported


def test_import_from_nothing(tmp_path, config, runner):
    path = tmp_path.joinpath("exported.yaml")
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    with path.open("w") as fp:
        yaml.dump(networks, fp)

    for key in config.networks.keys():
        runner.invoke(cli_networks.delete, [key])
    config.networks = {}

    runner.invoke(cli_networks.import_, [path.as_posix()])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    with path.open() as fp:
        exported = yaml.safe_load(fp)

    assert networks == exported


def test_import(tmp_path, runner):
    path = tmp_path.joinpath("exported.yaml")
    with path.open("w") as fp:
        yaml.dump(
            {
                "live": [
                    {
                        "name": "FooChain",
                        "networks": [
                            {"id": "tester", "host": "127.0.0.1", "chainid": 42, "name": "tester"}
                        ],
                    }
                ]
            },
            fp,
        )

    runner.invoke(cli_networks.import_, [path.as_posix()])

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert networks["live"][-1] == {
        "name": "FooChain",
        "networks": [{"id": "tester", "host": "127.0.0.1", "chainid": 42, "name": "tester"}],
    }


def test_import_id_exists(tmp_path, runner):
    path = tmp_path.joinpath("exported.yaml")
    with path.open("w") as fp:
        yaml.dump(
            {
                "live": [
                    {
                        "name": "FooChain",
                        "networks": [{"id": "mainnet", "host": "127.0.0.1", "chainid": 42}],
                    }
                ]
            },
            fp,
        )

    result = runner.invoke(cli_networks.import_, [path.as_posix()])
    assert isinstance(result.exception, ValueError) is True

