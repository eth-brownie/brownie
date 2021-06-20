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


def test_list(config, capfd):
    cli_networks._list(verbose=False)
    output = capfd.readouterr()[0]

    assert "chainid" not in output
    for key in config.networks:
        assert key in output


def test_list_verbose(config, capfd):
    cli_networks._list(verbose=True)
    output = capfd.readouterr()[0]

    assert "chainid" in output
    for key in config.networks:
        assert key in output


def test_add():
    cli_networks._add("ethereum", "tester", "host=127.0.0.1", "chainid=42")

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    assert networks["live"][0]["networks"][-1] == {
        "id": "tester",
        "host": "127.0.0.1",
        "chainid": 42,
        "name": "tester",
    }


def test_add_new_env():
    cli_networks._add("FooChain", "tester", "host=127.0.0.1", "chainid=42")

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    assert networks["live"][-1] == {
        "name": "FooChain",
        "networks": [{"id": "tester", "host": "127.0.0.1", "chainid": 42, "name": "tester"}],
    }


def test_add_exists():
    with pytest.raises(ValueError):
        cli_networks._add("FooChain", "development", "host=127.0.0.1", "chainid=42")


def test_add_missing_field():
    with pytest.raises(ValueError):
        cli_networks._add("FooChain", "tester", "chainid=42")


def test_add_unknown_field():
    with pytest.raises(ValueError):
        cli_networks._add("FooChain", "tester", "host=127.0.0.1", "chainid=42", "foo=bar")


def test_add_dev():
    cli_networks._add("development", "tester", "host=127.0.0.1", "cmd=foo", "port=411")

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    assert networks["development"][-1] == {
        "id": "tester",
        "host": "127.0.0.1",
        "cmd": "foo",
        "name": "tester",
        "cmd_settings": {"port": 411},
    }


def test_add_dev_missing_field():
    with pytest.raises(ValueError):
        cli_networks._add("development", "tester", "host=127.0.0.1" "port=411")


def test_add_dev_unknown_field():
    with pytest.raises(ValueError):
        cli_networks._add("development", "tester", "cmd=foo", "host=127.0.0.1" "chainid=411")


def test_modify():
    cli_networks._modify("mainnet", "chainid=3")
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert networks["live"][0]["networks"][0]["chainid"] == 3


def test_modify_id():
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        mainnet = yaml.safe_load(fp)["live"][0]["networks"][0]

    cli_networks._modify("mainnet", "id=foo")

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        foo = yaml.safe_load(fp)["live"][0]["networks"][0]

    mainnet["id"] = "foo"
    assert mainnet == foo


def test_modify_remove():
    cli_networks._modify("development", "port=None")
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert "port" not in networks["development"][0]["cmd_settings"]


def test_modify_add():
    cli_networks._modify("development", "fork=true")
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert "fork" in networks["development"][0]["cmd_settings"]


def test_modify_unknown():
    with pytest.raises(ValueError):
        cli_networks._modify("development", "foo=true")


def test_modify_remove_required():
    with pytest.raises(ValueError):
        cli_networks._modify("development", "id=None")


def test_delete_live():
    cli_networks._delete("mainnet")

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert "mainnet" not in [i["id"] for i in networks["live"][0]["networks"]]


def test_delete_development():
    for network_name in (
        "development",
        "mainnet-fork",
        "bsc-main-fork",
        "ftm-main-fork",
        "polygon-main-fork",
        "geth-dev",
    ):
        cli_networks._delete(network_name)

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert not networks["development"]


def test_delete_all_networks_in_prod_environment():
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    initial_networks = len(networks["live"])

    cli_networks._delete("etc")
    cli_networks._delete("kotti")

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    assert len(networks["live"]) == initial_networks - 1


def test_export(tmp_path):
    path = tmp_path.joinpath("exported.yaml")
    cli_networks._export(path.as_posix())

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    with path.open() as fp:
        exported = yaml.safe_load(fp)

    assert networks == exported


def test_import_from_nothing(tmp_path, config):
    path = tmp_path.joinpath("exported.yaml")
    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    with path.open("w") as fp:
        yaml.dump(networks, fp)

    for key in config.networks.keys():
        cli_networks._delete(key)
    config.networks = {}

    cli_networks._import(path.as_posix())

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)
    with path.open() as fp:
        exported = yaml.safe_load(fp)

    assert networks == exported


def test_import(tmp_path):
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

    cli_networks._import(path.as_posix())

    with _get_data_folder().joinpath("network-config.yaml").open() as fp:
        networks = yaml.safe_load(fp)

    assert networks["live"][-1] == {
        "name": "FooChain",
        "networks": [{"id": "tester", "host": "127.0.0.1", "chainid": 42, "name": "tester"}],
    }


def test_import_id_exists(tmp_path):
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

    with pytest.raises(ValueError):
        cli_networks._import(path.as_posix())
