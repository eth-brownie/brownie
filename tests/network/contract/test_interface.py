from brownie.network.contract import (
    Contract,
    InterfaceConstructor,
    InterfaceContainer,
    _get_deployment,
)


def test_interfacecontainer_add():
    interface = InterfaceContainer(None)
    interface._add("Test", [])

    assert hasattr(interface, "Test")
    assert isinstance(interface.Test, InterfaceConstructor)


def test_interfaceconstructor_call(tester):
    interface = InterfaceContainer(None)
    interface._add("Test", [{"type": "foo"}])

    contract = interface.Test(tester.address)

    assert isinstance(contract, Contract)
    assert contract.abi == [{"type": "foo"}]


def test_interface_is_not_persisted(network):
    network.connect("mainnet")
    interface = InterfaceContainer(None)
    interface._add("Test", [{"type": "foo"}])

    address = "0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e"
    interface.Test(address)
    assert _get_deployment(address) == (None, None)
