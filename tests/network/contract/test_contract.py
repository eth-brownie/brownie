#!/usr/bin/python3
from copy import deepcopy

import pytest
import yaml
from eth_retry import auto_retry
from semantic_version import Version
from vvm.utils.convert import to_vyper_version

import brownie.network.contract
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


EXPLORER_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "value",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "pure",
        "type": "function",
    }
]

EXPLORER_SOURCE = """
pragma solidity ^0.5.0;

contract HermeticExplorer {
    function value() external pure returns (uint256) {
        return 31337;
    }
}
"""

PRE_422_SOURCE = """
pragma solidity ^0.4.18;

contract DSToken {
    function value() public pure returns (uint256) {
        return 31337;
    }
}
"""

PROXY_SOURCE = """
pragma solidity ^0.4.18;

contract ProxyContract {
}
"""

VYPER_SOURCE = """
# @version 0.4.3

@external
@view
def value() -> uint256:
    return 31337
"""


def _mock_solc_versions(monkeypatch, *versions):
    monkeypatch.setattr(
        brownie.network.contract.solcx,
        "get_installable_solc_versions",
        lambda: [Version(str(version)) for version in versions],
    )


def _mock_vyper_versions(monkeypatch, *versions):
    monkeypatch.setattr(
        brownie.network.contract,
        "get_installable_vyper_versions",
        lambda: [to_vyper_version(str(version)) for version in versions],
    )


def _mock_verified_code(monkeypatch):
    monkeypatch.setattr(
        brownie.network.contract,
        "_verify_deployed_code",
        lambda _address, _expected_bytecode, _language: True,
    )


def test_type_solidity(tester):
    assert type(tester) is ProjectContract
    assert isinstance(tester, _DeployedContractBase)


def test_type_vyper(vypertester):
    assert type(vypertester) is ProjectContract
    assert isinstance(vypertester, _DeployedContractBase)


@auto_retry
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


@auto_retry
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


@auto_retry
def test_contractabi_replace_contract(testproject, tester):
    Contract.from_abi("BrownieTester", tester.address, tester.abi)
    del testproject.BrownieTester[0]
    Contract.from_abi("BrownieTester", tester.address, tester.abi)
    Contract.from_abi("BrownieTester", tester.address, tester.abi)


@auto_retry
def test_deprecated_init_abi(tester):
    with pytest.warns(DeprecationWarning):
        old = Contract("BrownieTester", tester.address, tester.abi)

    assert old == Contract.from_abi("BrownieTester", tester.address, tester.abi)


def test_from_explorer(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.5.17")
    _mock_verified_code(monkeypatch)
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000101",
        name="HermeticExplorer",
        abi=EXPLORER_ABI,
        source=EXPLORER_SOURCE,
        compiler_version="v0.5.17",
    )

    contract = Contract.from_explorer(address)

    assert contract._name == "HermeticExplorer"
    assert "pcMap" in contract._build
    assert len(contract._sources) == 1
    assert mock_explorer.actions(address) == ["getsourcecode"]


def test_from_explorer_only_abi(mock_explorer):
    address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000102", abi=EXPLORER_ABI
    )

    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer(address)

    assert contract._name == "UnknownContractName"
    assert "pcMap" not in contract._build
    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]


def test_from_explorer_pre_422(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.4.18")
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000103",
        name="DSToken",
        abi=EXPLORER_ABI,
        source=PRE_422_SOURCE,
        compiler_version="v0.4.18",
    )

    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer(address)

    assert contract._name == "DSToken"
    assert "pcMap" not in contract._build


def test_from_explorer_vyper_supported(mock_explorer, monkeypatch):
    _mock_vyper_versions(monkeypatch, "0.4.3")
    _mock_verified_code(monkeypatch)
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000104",
        name="Vyper_contract",
        abi=EXPLORER_ABI,
        source=VYPER_SOURCE,
        compiler_version="vyper:0.4.3",
        optimization_used="0",
    )

    contract = Contract.from_explorer(address)

    assert contract._name == "Vyper_contract"
    assert "pcMap" in contract._build


def test_from_explorer_vyper_old_version(mock_explorer, monkeypatch):
    _mock_vyper_versions(monkeypatch, "0.4.3")
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000105",
        name="Vyper_contract",
        abi=EXPLORER_ABI,
        source=VYPER_SOURCE,
        compiler_version="vyper:0.1.0-beta.4",
        optimization_used="0",
    )

    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer(address)

    assert contract._name == "Vyper_contract"
    assert "pcMap" not in contract._build


def test_from_explorer_unverified(mock_explorer):
    address = mock_explorer.add_unverified("0x0000000000000000000000000000000000000106")

    with pytest.raises(ValueError):
        Contract.from_explorer(address)

    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]


@pytest.mark.skip(
    "etc rpc fails to connect and blocks the test runner while retrying. "
    "Maybe fix this test with a different network."
)
@auto_retry
def test_from_explorer_etc(network):
    network.connect("etc")
    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer("0x085b0fdf115aa9e16ae1bddd396ce1f993c52220")

    assert contract._name == "ONEX"


def test_retrieve_existing(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.4.18")
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000107",
        name="DSToken",
        abi=EXPLORER_ABI,
        source=PRE_422_SOURCE,
        compiler_version="v0.4.18",
    )

    with pytest.warns(BrownieCompilerWarning):
        new = Contract.from_explorer(address)

    existing = Contract(address)
    assert new == existing


@auto_retry
@pytest.mark.skip(reason="Goerli on Infura is dead - the test suite needs a refactor")
def test_existing_different_chains(network, connect_to_mainnet):
    with pytest.warns(BrownieCompilerWarning):
        Contract.from_explorer("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")

    network.disconnect()
    network.connect("goerli")
    with pytest.raises(ValueError):
        Contract("0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2")


def test_alias(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.4.18")
    address = mock_explorer.add_source(
        "0x0000000000000000000000000000000000000108",
        name="DSToken",
        abi=EXPLORER_ABI,
        source=PRE_422_SOURCE,
        compiler_version="v0.4.18",
    )

    with pytest.warns(BrownieCompilerWarning):
        contract = Contract.from_explorer(address)

    contract.set_alias("testalias")

    assert contract.alias == "testalias"
    assert Contract("testalias") == contract

    contract.set_alias(None)

    assert contract.alias is None
    with pytest.raises(ValueError):
        Contract("testalias")


def test_alias_not_exists(mock_explorer):
    with pytest.raises(ValueError):
        Contract("doesnotexist")


def test_duplicate_alias(mock_explorer):
    foo_address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000109", abi=EXPLORER_ABI
    )
    bar_address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000110", abi=EXPLORER_ABI
    )

    with pytest.warns(BrownieCompilerWarning):
        foo = Contract.from_explorer(foo_address)
    with pytest.warns(BrownieCompilerWarning):
        bar = Contract.from_explorer(bar_address)

    foo.set_alias("foo")
    with pytest.raises(ValueError):
        bar.set_alias("foo")

    bar.set_alias("bar")
    foo.set_alias(None)
    bar.set_alias("foo")


@auto_retry
def test_alias_in_development(tester):
    contract = Contract.from_abi("BrownieTester", tester.address, tester.abi)

    with pytest.raises(ValueError):
        contract.set_alias("testalias")


def test_autofetch(config, mock_explorer):
    address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000111", abi=EXPLORER_ABI
    )

    with pytest.raises(ValueError):
        Contract(address)

    config.settings["autofetch_sources"] = True
    Contract(address)
    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]


def test_autofetch_missing(config, mock_explorer):
    config.settings["autofetch_sources"] = True
    address = mock_explorer.add_unverified(
        "0xff031750F29b24e6e5552382F6E0c065830085d2"
    )

    with pytest.raises(ValueError):
        Contract(address)
    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]

    with pytest.raises(ValueError):
        Contract(address)
    assert mock_explorer.actions(address) == ["getsourcecode", "getabi"]


def test_as_proxy_for(mock_explorer, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.4.18")
    proxy_address = "0x0000000000000000000000000000000000000112"
    impl_address = "0x0000000000000000000000000000000000000113"
    expected_proxy = brownie.network.contract._resolve_address(proxy_address)
    mock_explorer.add_source(
        impl_address,
        name="DSToken",
        abi=EXPLORER_ABI,
        source=PRE_422_SOURCE,
        compiler_version="v0.4.18",
    )
    mock_explorer.add_source(
        proxy_address,
        name="ProxyContract",
        abi=[],
        source=PROXY_SOURCE,
        compiler_version="v0.4.18",
        implementation=impl_address,
    )

    with pytest.warns(BrownieCompilerWarning):
        auto_proxy = Contract.from_explorer(proxy_address)
    with pytest.warns(BrownieCompilerWarning):
        explicit_proxy = Contract.from_explorer(proxy_address, as_proxy_for=impl_address)
    implementation = Contract(impl_address)

    assert auto_proxy.abi == explicit_proxy.abi == implementation.abi
    assert hasattr(auto_proxy, "value")
    assert hasattr(explicit_proxy, "value")
    assert auto_proxy.address == explicit_proxy.address == expected_proxy
    assert auto_proxy.address != implementation.address
    assert mock_explorer.actions(proxy_address) == ["getsourcecode", "getsourcecode"]
    assert mock_explorer.actions(impl_address) == ["getsourcecode", "getsourcecode"]
    assert set(mock_explorer.actions()) == {"getsourcecode"}


def test_solc_use_latest_patch_true(testproject, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.5.0", "0.4.26", "0.4.16")
    solc_config = {"compiler": {"solc": {"use_latest_patch": True}}}
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.26")


def test_solc_use_latest_patch_false(testproject):
    solc_config = {"compiler": {"solc": {"use_latest_patch": False}}}
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.16")


def test_solc_use_latest_patch_missing(testproject):
    solc_config = {"compiler": {"solc": {}}}
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.16")


def test_solc_use_latest_patch_specific_not_included(testproject):
    solc_config = {
        "compiler": {"solc": {"use_latest_patch": ["0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e"]}}
    }
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.16")


def test_solc_use_latest_patch_specific_included(testproject, monkeypatch):
    _mock_solc_versions(monkeypatch, "0.5.0", "0.4.26", "0.4.16")
    solc_config = {
        "compiler": {"solc": {"use_latest_patch": ["0x514910771AF9Ca656af840dff83E8264EcF986CA"]}}
    }
    with testproject._path.joinpath("brownie-config.yaml").open("w") as fp:
        yaml.dump(solc_config, fp)

    assert Contract.get_solc_version(
        "v0.4.16", "0x514910771AF9Ca656af840dff83E8264EcF986CA"
    ) == Version("0.4.26")


def test_abi_deployment_enabled_by_default(build, mock_explorer):
    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    mock_explorer.set_code(address)
    Contract.from_abi("abiTester", address, build["abi"])

    assert _get_deployment(address) != (None, None)
    # cleanup
    Contract.remove_deployment(address)


def test_abi_deployment_disabled(build, mock_explorer):
    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    mock_explorer.set_code(address)
    Contract.from_abi("abiTester", address, build["abi"], persist=False)

    assert _get_deployment(address) == (None, None)


def test_from_explorer_deployment_enabled_by_default(mock_explorer):
    address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000112", abi=EXPLORER_ABI
    )

    with pytest.warns(BrownieCompilerWarning):
        Contract.from_explorer(address)

    assert _get_deployment(address) != (None, None)
    # cleanup
    Contract.remove_deployment(address)


def test_from_explorer_deployment_disabled(mock_explorer):
    address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000113", abi=EXPLORER_ABI
    )

    with pytest.warns(BrownieCompilerWarning):
        Contract.from_explorer(address, persist=False)

    assert _get_deployment(address) == (None, None)


def test_remove_deployment(mock_explorer):
    address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000114", abi=EXPLORER_ABI
    )

    with pytest.warns(BrownieCompilerWarning):
        Contract.from_explorer(address)

    Contract.remove_deployment(address)

    assert _get_deployment(address) == (None, None)


def test_remove_deployment_returns(mock_explorer):
    address = mock_explorer.add_abi_only(
        "0x0000000000000000000000000000000000000115", abi=EXPLORER_ABI
    )

    with pytest.warns(BrownieCompilerWarning):
        Contract.from_explorer(address)

    build_json, sources = _get_deployment(address)

    assert (build_json, sources) != (None, None)
    assert (build_json, sources) == (Contract.remove_deployment(address))
