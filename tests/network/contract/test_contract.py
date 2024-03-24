#!/usr/bin/python3
from copy import deepcopy

import pytest
import requests
import yaml
from semantic_version import Version

from brownie import Wei
from brownie.exceptions import BrownieCompilerWarning, BrownieEnvironmentWarning, ContractNotFound
from brownie.network.contract import (
    Contract,
    ContractCall,
    ContractTx,
    ProjectContract,
    _DeployedContractBase,
    _get_deployment,
)


@pytest.fixture
def build(testproject):
    build = testproject._build.get("BrownieTester")
    yield deepcopy(build)


def test_type_solidity(tester):
    assert type(tester) is ProjectContract
    assert isinstance(tester, _DeployedContractBase)


def test_type_vyper(vypertester):
    assert type(vypertester) is ProjectContract
    assert isinstance(vypertester, _DeployedContractBase)


def test_namespace_collision(tester, build):
    build["abi"].append(
        {
            "constant": False,
            "inputs": [
                {"name": "_to", "type": "address"},
                {"name": "_value", "type": "uint256"},
                {"name": "_test", "type": "uint256"},
            ],
            "name": "bytecode",
            "outputs": [{"name": "", "type": "bool"}],
            "payable": False,
            "stateMutability": "nonpayable",
            "type": "function",
        }
    )
    with pytest.warns(BrownieEnvironmentWarning):
        Contract.from_abi(None, tester.address, build["abi"])


def test_set_methods(tester):
    for item in tester.abi:
        if item["type"] != "function":
            if "name" not in item:
                continue
            assert not hasattr(tester, item["name"])
        elif item["stateMutability"] in ("view", "pure"):
            assert type(getattr(tester, item["name"])) == ContractCall
        else:
            assert type(getattr(tester, item["name"])) == ContractTx


def test_balance(tester):
    balance = tester.balance()
    assert type(balance) is Wei
    assert balance == "0 ether"


def test_comparison(testproject, tester):
    del testproject.BrownieTester[0]
    assert tester != 123
    assert tester == str(tester.address)
    assert tester == Contract.from_abi("BrownieTester", tester.address, tester.abi)
    repr(tester)


def test_revert_not_found(tester, chain):
    chain.reset()
    with pytest.raises(ContractNotFound):
        tester.balance()


def test_contractabi_replace_contract(testproject, tester):
    Contract.from_abi("BrownieTester", tester.address, tester.abi)
    del testproject.BrownieTester[0]
    Contract.from_abi("BrownieTester", tester.address, tester.abi)
    Contract.from_abi("BrownieTester", tester.address, tester.abi)


def test_deprecated_init_abi(tester):
    with pytest.warns(DeprecationWarning):
        old = Contract("BrownieTester", tester.address, tester.abi)

    assert old == Contract.from_abi("BrownieTester", tester.address, tester.abi)


def test_from_explorer(network):
    network.connect("mainnet")
    contract = Contract.from_explorer("0x973e52691176d36453868d9d86572788d27041a9")

    assert contract._name == "DxToken"
    assert "pcMap" in contract._build
    assert len(contract._sources) == 1


@pytest.mark.xfail
def test_from_explorer_only_abi(network):
    network.connect("mainnet")
    # uniswap DAI market - ABI is available but source is not
    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer("0x2a1530C4C41db0B0b2bB646CB5Eb1A67b7158667")

    assert contract._name == "UnknownContractName"
    assert "pcMap" not in contract._build


def test_from_explorer_pre_422(network):
    network.connect("mainnet")

    # MKR, compiler version 0.4.18
    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")
    assert contract._name == "DSToken"
    assert "pcMap" not in contract._build


def test_from_explorer_vyper_supported_020(network):
    network.connect("mainnet")

    # curve yCRV gauge - `0.2.4`
    contract = Contract.from_explorer("0xFA712EE4788C042e2B7BB55E6cb8ec569C4530c1")

    assert contract._name == "Vyper_contract"
    assert "pcMap" in contract._build


def test_from_explorer_vyper_supported_010(network):
    network.connect("mainnet")

    # curve cDAI/cUSDC - `0.1.0-beta.16`
    contract = Contract.from_explorer("0x845838DF265Dcd2c412A1Dc9e959c7d08537f8a2")

    assert contract._name == "Vyper_contract"
    assert "pcMap" in contract._build


def test_from_explorer_vyper_old_version(network):
    network.connect("mainnet")
    with pytest.warns(BrownieCompilerWarning):
        # uniswap v1 - `0.1.0-beta.4`
        contract = Contract.from_explorer("0x2157a7894439191e520825fe9399ab8655e0f708")

    assert contract._name == "Vyper_contract"
    assert "pcMap" not in contract._build


def test_from_explorer_unverified(network):
    network.connect("mainnet")
    with pytest.raises(ValueError):
        Contract.from_explorer("0x0000000000000000000000000000000000000000")


@pytest.mark.xfail
def test_from_explorer_etc(network):
    network.connect("etc")
    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer("0x085b0fdf115aa9e16ae1bddd396ce1f993c52220")

    assert contract._name == "ONEX"


def test_retrieve_existing(network):
    network.connect("mainnet")
    with pytest.warns(BrownieCompilerWarning):
        new = Contract.from_explorer("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")

    existing = Contract("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")
    assert new == existing


@pytest.mark.xfail(reason="Infura rate limiting - the test suite needs a refactor", strict=False)
def test_existing_different_chains(network):
    network.connect("mainnet")
    with pytest.warns(BrownieCompilerWarning):
        Contract.from_explorer("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")

    network.disconnect()
    network.connect("goerli")
    with pytest.raises(ValueError):
        Contract("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")


def test_alias(network):
    network.connect("mainnet")
    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")

    contract.set_alias("testalias")

    assert contract.alias == "testalias"
    assert Contract("testalias") == contract

    contract.set_alias(None)

    assert contract.alias is None
    with pytest.raises(ValueError):
        Contract("testalias")


def test_alias_not_exists(network):
    network.connect("mainnet")

    with pytest.raises(ValueError):
        Contract("doesnotexist")


def test_duplicate_alias(network):
    network.connect("mainnet")

    foo = Contract.from_explorer("0x2af5d2ad76741191d15dfe7bf6ac92d4bd912ca3")
    with pytest.warns(BrownieCompilerWarning):
        bar = Contract.from_explorer("0x2157a7894439191e520825fe9399ab8655e0f708")

    foo.set_alias("foo")
    with pytest.raises(ValueError):
        bar.set_alias("foo")

    bar.set_alias("bar")
    foo.set_alias(None)
    bar.set_alias("foo")


def test_alias_in_development(tester):
    contract = Contract.from_abi("BrownieTester", tester.address, tester.abi)

    with pytest.raises(ValueError):
        contract.set_alias("testalias")


def test_autofetch(network, config):
    network.connect("mainnet")
    with pytest.raises(ValueError):
        Contract("0xdAC17F958D2ee523a2206206994597C13D831ec7")

    config.settings["autofetch_sources"] = True
    Contract("0xdAC17F958D2ee523a2206206994597C13D831ec7")


def test_autofetch_missing(network, config, mocker):
    # an issue woth pytest-mock prevents spying on Contract.from_explorer,
    # so we watch requests.get which is only called inside Contract.from_explorer
    mocker.spy(requests, "get")

    network.connect("mainnet")
    config.settings["autofetch_sources"] = True

    with pytest.raises(ValueError):
        Contract("0xff031750F29b24e6e5552382F6E0c065830085d2")
    assert requests.get.call_count == 2

    with pytest.raises(ValueError):
        Contract("0xff031750F29b24e6e5552382F6E0c065830085d2")
    assert requests.get.call_count == 2


def test_as_proxy_for(network):
    proxy = "0x2410B710ecA3818003c091c42E3803cC7D70AeE9"
    impl = "0x7542fb54dc0c2d71a00d9409b48f5e464b5e9f24"
    network.connect("goerli")

    original = Contract.from_explorer(proxy)
    proxy = Contract.from_explorer(proxy, as_proxy_for=impl)
    implementation = Contract(impl)

    assert original.abi == proxy.abi
    assert original.address == proxy.address

    assert proxy.abi == implementation.abi
    assert proxy.address != implementation.address


def test_solc_use_latest_patch_true(testproject, network):
    network.connect("mainnet")
    solc_config = {"compiler": {"solc": {"use_latest_patch": True}}}
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.26")


def test_solc_use_latest_patch_false(testproject, network):
    network.connect("mainnet")
    solc_config = {"compiler": {"solc": {"use_latest_patch": False}}}
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.16")


def test_solc_use_latest_patch_missing(testproject, network):
    network.connect("mainnet")
    solc_config = {"compiler": {"solc": {}}}
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.16")


def test_solc_use_latest_patch_specific_not_included(testproject, network):
    network.connect("mainnet")
    solc_config = {
        "compiler": {"solc": {"use_latest_patch": ["0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e"]}}
    }
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.16")


def test_solc_use_latest_patch_specific_included(testproject, network):
    network.connect("mainnet")
    solc_config = {
        "compiler": {"solc": {"use_latest_patch": ["0x514910771AF9Ca656af840dff83E8264EcF986CA"]}}
    }
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.26")


def test_abi_deployment_enabled_by_default(network, build):
    network.connect("mainnet")
    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    Contract.from_abi("abiTester", address, build["abi"])

    assert _get_deployment(address) != (None, None)
    # cleanup
    Contract.remove_deployment(address)


def test_abi_deployment_disabled(network, build):
    network.connect("mainnet")
    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    Contract.from_abi("abiTester", address, build["abi"], persist=False)

    assert _get_deployment(address) == (None, None)


def test_from_explorer_deployment_enabled_by_default(network):
    network.connect("mainnet")
    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    Contract.from_explorer(address)

    assert _get_deployment(address) != (None, None)
    # cleanup
    Contract.remove_deployment(address)


def test_from_explorer_deployment_disabled(network):
    network.connect("mainnet")
    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    Contract.from_explorer(address, persist=False)

    assert _get_deployment(address) == (None, None)


def test_remove_deployment(network):
    network.connect("mainnet")
    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    Contract.from_explorer(address)
    Contract.remove_deployment(address)

    assert _get_deployment(address) == (None, None)


def test_remove_deployment_returns(network):
    network.connect("mainnet")
    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    Contract.from_explorer(address)
    build_json, sources = _get_deployment(address)

    assert (build_json, sources) != (None, None)
    assert (build_json, sources) == (Contract.remove_deployment(address))


# @pytest.mark.parametrize(
#     "original",
#     [
#         "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b",  # comptroller
#         "0xEd0bEdA6991Ac426de442C84cee19d75aB78d2CE",  # aaragondao
#     ],
# )
# def test_as_proxy_for(network, original):
#     network.connect("mainnet")
#     original = Contract.from_explorer(original)
#
#     # fetch implementation from etherscan
#     API_URL = "https://api.etherscan.io/api"
#     params = {
#         "apikey": os.getenv("ETHERSCAN_TOKEN"),
#         "address": original,
#         "module": "contract",
#         "action": "verifyproxycontract",
#     }
#     response = requests.post(API_URL, params=params, headers=REQUEST_HEADERS)
#     if response.json()["status"] == "1":
#         guid = response.json()["result"]
#     else:
#         raise ValueError("Could not fetch proxy implementation.")
#
#     # wait for result
#     params = {
#         "apikey": os.getenv("ETHERSCAN_TOKEN"),
#         "guid": guid,
#         "module": "contract",
#         "action": "checkproxyverification",
#     }
#     impl = None
#     for _ in range(5):
#         response = requests.get(API_URL, params=params, headers=REQUEST_HEADERS)
#         data = response.json()
#         print(data)
#         if data["status"] == "1":
#             addresses = re.findall(r"0x[a-fA-F0-9]{40}", data["result"])
#             if len(addresses) < 2:
#                 raise ValueError("Could not fetch proxy implementation.")
#             impl = addresses[1]
#             break
#         elif data["result"] != "Pending in queue":
#             raise ValueError("Could not fetch proxy implementation.")
#         time.sleep(10)
#
#     if not impl:
#         raise ValueError("Could not fetch proxy implementation.")
#
#     # compare abis
#     proxy = Contract.from_explorer(original, as_proxy_for=impl)
#     implementation = Contract(impl)
#
#     assert original.abi == proxy.abi
#     assert original.address == proxy.address
#
#     assert proxy.abi == implementation.abi
#     assert proxy.address != implementation.address
