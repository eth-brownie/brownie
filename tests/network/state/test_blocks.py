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
