import pytest


def test_length(devnetwork, chain):
    assert len(chain) == 1
    chain.mine(4)
    assert len(chain) == 5


def test_length_after_revert(devnetwork, chain):
    chain.mine(4)
    chain.snapshot()
    chain.mine(20)
    assert len(chain) == 25

    chain.revert()
    assert len(chain) == 5


def test_timestamp(devnetwork, chain):
    chain.mine()
    assert chain[-2].timestamp <= chain[-1].timestamp


def test_timestamp_multiple_blocks(devnetwork, chain):
    chain.mine(5)
    for i in range(1, len(chain)):
        assert chain[i - 1].timestamp <= chain[i].timestamp


def test_getitem_negative_index(devnetwork, accounts, chain, web3):
    block = chain[-1]
    assert block == web3.eth.get_block("latest")

    accounts[0].transfer(accounts[1], 1000)

    assert chain[-1] != block
    assert chain[-1] == web3.eth.get_block("latest")


def test_getitem_positive_index(devnetwork, accounts, chain, web3):
    block = chain[0]
    assert block == web3.eth.get_block("latest")

    accounts[0].transfer(accounts[1], 1000)

    assert chain[0] == block
    assert chain[0] != web3.eth.get_block("latest")


def test_mine_timestamp(devnetwork, chain):
    chain.mine(timestamp=999999999999)

    assert chain[-1].timestamp == 999999999999
    assert chain.time() - 999999999999 < 3


def test_mine_timestamp_next_block(devnetwork, chain):
    chain.mine(timestamp=999999999999)
    chain.mine()

    assert chain[-1].timestamp >= 999999999999
    assert chain.time() >= 999999999999


def test_mine_timedelta(devnetwork, chain):
    now = chain.time()
    chain.mine(timedelta=12345)

    assert 0 <= chain[-1].timestamp - 12345 - now <= 1


def test_mine_timedelta_next_block(devnetwork, chain):
    now = chain.time()
    chain.mine(timedelta=12345)
    chain.mine()

    assert chain[-1].timestamp >= now + 12345
    assert chain.time() >= now + 12345


def test_mine_multiple_timestamp(devnetwork, chain):
    chain.mine(5, timestamp=chain.time() + 123)
    timestamps = [i.timestamp for i in list(chain)[-5:]]

    assert chain.time() - timestamps[-1] < 3

    for i in range(1, 5):
        assert timestamps[i] > timestamps[i - 1]

    assert timestamps[0] + 123 == timestamps[-1]


def test_mine_multiple_timedelta(devnetwork, chain):
    chain.mine(5, timedelta=123)
    timestamps = [i.timestamp for i in list(chain)[-5:]]

    assert chain.time() - timestamps[-1] < 3

    for i in range(1, 5):
        assert timestamps[i] > timestamps[i - 1]

    assert timestamps[0] + 123 == timestamps[-1]


def test_mine_timestamp_and_timedelta(devnetwork, chain):
    with pytest.raises(ValueError):
        chain.mine(timestamp=12345, timedelta=31337)
