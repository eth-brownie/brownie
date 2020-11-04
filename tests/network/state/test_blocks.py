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


def test_getitem_negative_index(devnetwork, accounts, chain, web3):
    block = chain[-1]
    assert block == web3.eth.getBlock("latest")

    accounts[0].transfer(accounts[1], 1000)

    assert chain[-1] != block
    assert chain[-1] == web3.eth.getBlock("latest")


def test_getitem_positive_index(devnetwork, accounts, chain, web3):
    block = chain[0]
    assert block == web3.eth.getBlock("latest")

    accounts[0].transfer(accounts[1], 1000)

    assert chain[0] == block
    assert chain[0] != web3.eth.getBlock("latest")


def test_mine_timestamp(devnetwork, chain):
    chain.mine(timestamp=12345)

    assert chain[-1].timestamp == 12345
    assert chain.time() - 12345 < 3


def test_mine_multiple_timestamp(devnetwork, chain):
    chain.mine(5, timestamp=chain.time() + 123)
    timestamps = [i.timestamp for i in list(chain)[-5:]]

    assert chain.time() - timestamps[-1] < 3

    for i in range(1, 5):
        assert timestamps[i] > timestamps[i - 1]

    assert timestamps[0] + 123 == timestamps[-1]
