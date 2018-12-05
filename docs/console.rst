=================
Using The Console
=================

The console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop.

The console feels similar to a normal python interpreter. Load it by typing:

::

    $ brownie console


The container ``accounts`` allows you to access all your local accounts:

.. code-block:: python

    >>> accounts[0]
    <Account object '0xC0BcE0346d4d93e30008A1FE83a2Cf8CfB9Ed301'>
    >>> accounts[1].balance()
    100000000000000000000
    >>> accounts[0].transfer(accounts[1], "10 ether")

    Transaction sent: 0x124ba3f9f9e5a8c5e7e559390bebf8dfca998ef32130ddd114b7858f255f6369
    Transaction confirmed - block: 1   gas spent: 21000
    <Transaction object '0x124ba3f9f9e5a8c5e7e559390bebf8dfca998ef32130ddd114b7858f255f6369'>
    >>> accounts[1].balance()
    110000000000000000000

Each contract in the project has a ``ContractDeployer`` class, which allows you to deploy new contracts and is a container that holds specific instances of that contract:

.. code-block:: python

    >>> Token
    <Token ContractDeployer object>
    >>> accounts[0].deploy(Token, "Test Token", "TST", 18, "1000 ether")

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 2   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>> Token[0]
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

You can also use ``ContractDeployer.at`` to access an already existing contract:

.. code-block:: python

    >>> Token.at("0x5419710735c2D6c3e4db8F30EF2d361F70a4b380")
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

To call a contract or send a transaction:

.. code-block:: python

    >>> Token[0].balanceOf(accounts[0])
    1000000000000000000000
    >>> Token[0].transfer(accounts[1],"10 ether", {'from':accounts[0]})

    Transaction sent: 0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532
    Transaction confirmed - block: 3   gas spent: 51241
    <Transaction object '0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532'>
    >>> Token[0].balanceOf(accounts[1])
    10000000000000000000

You can access the ``Web3.py`` library:

.. code-block:: python

    >>> eth
    <web3.eth.Eth object at 0x7facfa6e5c50>
    >>> net
    <web3.net.Net object at 0x7facfd050cc0>
    >>> sha3
    <function Web3.sha3 at 0x7facfa6e3ae8>


Use ``wei`` to convert values to wei:

.. code-block:: python

    >>> wei("15.33 ether")
    15330000000000000000
    >>> wei(1.533e19)
    15330000000000000000
    >>> wei(1.3829e36)
    1382900000000000000000000000000000000
    >>> wei("8.26 shannon")
    8260000000
