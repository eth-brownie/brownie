=================
Using The Console
=================

The console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop.

The console feels similar to a normal python interpreter. Load it by typing:

::

    $ brownie console

Brownie will compile your contracts, start the local RPC, and then give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`. Below are some examples of common tasks.

Basic Functionality
===================

The following methods and classes are available:

* ``logging(tx=None, exc=None)``: Adjusts the console verbosity.
* ``reset(network=None)``: Reset the local RPC environment.
* ``run(script)``: Runs a deployment script.
* ``wei(value)``: Converts strings and floats to an integer denoted in wei
* ``web3``: A minimal implementation of the Web3.py `Web3 API <https://web3py.readthedocs.io/en/stable/web3.main.html>`__

Working with Accounts
=====================

The container class ``accounts`` (or just ``a``) allows you to access all your local accounts:

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

You can import accounts with ``accounts.add``, which takes a private key as the only argument:

.. code-block:: python

    >>> len(accounts)
    20
    >>> accounts.add("ce7594141801cf9b81b7ccb09e30395fc9e9e5940b1c01eed6434588bd726f94")
    <Account object '0x405De4AeCb9c1cE75152F82F956E09F4eda3b351'>
    >>> len(accounts)
    21
    >>> accounts[20]
    <Account object '0x405De4AeCb9c1cE75152F82F956E09F4eda3b351'>

Working with Contracts
======================

Each contract in the project has a ``ContractDeployer`` class, which allows you to deploy new contracts and is a container that holds specific instances of that contract. To deploy a contract, include the deploying account as the first argument followed by the constructor arguments:

.. code-block:: python

    >>> Token
    <Token ContractDeployer object>
    >>> Token.deploy(accounts[1], "Test Token", "TST", 18, "1000 ether")

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 2   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>> Token[0]
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

Alternatively, you can deploy from ``account`` with the contract as the first argument:

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

You can call any available contract method or send a transaction by using the class method of the same name, with the intended arguments.

For transactions you can optionally include a dictionary of `transaction parameters <https://web3py.readthedocs.io/en/stable/web3.eth.html#web3.eth.Eth.sendTransaction>`__ as the final argument. If you omit this or do not specify a ``'from'`` value, the transaction will be sent from the same address that deployed the contract.

.. code-block:: python

    >>> Token[0].balanceOf
    <ContractCall object 'balanceOf(address)'>
    >>> Token[0].balanceOf(accounts[0])
    1000000000000000000000
    >>> Token[0].transfer
    <ContractTx object 'transfer(address,uint256)'>
    >>> Token[0].transfer(accounts[1], "10 ether", {'from':accounts[0]})

    Transaction sent: 0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532
    Transaction confirmed - block: 3   gas spent: 51241
    <Transaction object '0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532'>
    >>> Token[0].balanceOf(accounts[1])
    10000000000000000000
