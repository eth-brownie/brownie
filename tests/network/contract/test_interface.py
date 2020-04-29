from brownie.network.contract import Contract, InterfaceConstructor, InterfaceContainer


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
