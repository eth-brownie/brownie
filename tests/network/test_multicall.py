from brownie import multicall


def test_proxy_update(tester, multicall2):
    result = None
    with multicall(multicall2.address) as call:
        result = call(tester).doNothing()
        assert not isinstance(result, bool)
    assert isinstance(result, bool)


def test_read_from_block(vypertester, multicall2, history, accounts):
    for num in range(4, 0, -1):
        vypertester.outOfBounds(0, num, {"from": accounts[0]})

    block_number = history[-4].block_number
    with multicall(multicall2.address, block_number) as call:
        result = call(vypertester).stuff(0)
    assert result == 4


def test_get_complex_structure(tester, accounts, multicall2):
    value = ["blahblah", accounts[1], ["yesyesyes", "0x1234"]]
    tester.setTuple(value)

    with multicall(multicall2.address) as call:
        result = call(tester).getTuple(accounts[1])
    assert result == value


def test_returns_none_for_reverting_calls(tester, multicall2):
    with multicall(multicall2.address) as call:
        result = call(tester).revertStrings(0)
    assert result.__wrapped__ is None
