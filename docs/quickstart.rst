.. _quickstart:

==========
Quickstart
==========

This page will walk you through the basics of using Brownie. Please review the rest of the documentation to learn more about specific functionality.

Initializing a New Project
==========================

The first step to using Brownie is to initialize a new project. To do this, create a new empty folder and then type:

::

    $ brownie init

This will create the following project structure within the folder:

* ``build/``: Compiled contracts and test data
* ``contracts/``: Contract source code
* ``scripts/``: Scripts for deployment and interaction
* ``tests/``: Scripts for testing your project
* ``brownie-config.json``: Configuration file for the project

You can also initialize "`Brownie mixes <https://github.com/brownie-mix>`__", simple templates to build your project upon. For the purposes of this document, we will use the `token <https://github.com/brownie-mix/token-mix>`__ mix, which is a very basic ERC-20 implementation:

::

    $ brownie bake token

This creates a new folder ``token/`` and deploys the project inside it.

Compiling your Contracts
========================

To compile your project:

::

    $ brownie compile

You will see the following output:

::

    Brownie v1.0.0 - Python development framework for Ethereum

    Compiling contracts...
    Optimizer: Enabled  Runs: 200
    - Token.sol...
    - SafeMath.sol...
    Brownie project has been compiled at token/build/contracts

Once a contract has been complied, it will only be recompiled if the source file has changed.

Interacting with your Project
=============================

The Brownie console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop. It feels similar to the standard python interpreter. To open it:

::

    $ brownie console

Brownie will compile your contracts, start the local RPC, and then give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`.

.. hint::

    You can use builtins ``dir`` and ``help`` for quick reference to available methods and attributes.

Here is an example of checking a balance and transfering some ether:

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

Deploying a contract:

.. code-block:: python

    >>> Token
    []
    >>> Token.deploy
    <ContractConstructor object 'Token.constructor(string _symbol, string _name, uint256 _decimals, uint256 _totalSupply)'>
    >>> t = Token.deploy(accounts[1], "Test Token", "TST", 18, "1000 ether")

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 1   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>>
    >>> t
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>

Checking a token balance and transfering tokens:

.. code-block:: python

    >>> t
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>> t.balanceOf(accounts[1])
    1000000000000000000000

    >>> t.transfer
    <ContractTx object 'transfer(address _to, uint256 _value)'>
    >>> t.transfer(accounts[2], "100 ether", {'from': accounts[1]})

    Transaction sent: 0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532
    Transaction confirmed - block: 2   gas spent: 51241
    <Transaction object '0xcd98225a77409b8d81023a3a4be15832e763cd09c74ff431236bfc6d56a74532'>
    >>>
    >>> t.balanceOf(accounts[1])
    900000000000000000000
    >>> t.balanceOf(accounts[2])
    100000000000000000000

Running Scripts
===============

You can write scripts to automate contract deployment and interaction:

::

    $ brownie run

Within the token project, you will find an example script at `scripts/token.py <https://github.com/brownie-mix/token-mix/blob/master/scripts/token.py>`__ that is used for deployment:

.. code-block:: python
    :linenos:

    from brownie import *

    def main():
        accounts[0].deploy(Token, "Test Token", "TEST", 18, "1000 ether")

This deploys the ``Token`` contract from ``contracts/Token.sol`` using ``web3.eth.accounts[0]``.

Testing your Project
====================

To run all of the test scripts in ``tests/``:

::

    $ brownie test

Running it in the token project, you will receive output similar to the following:

::

    Brownie v1.0.0 - Python development framework for Ethereum

    Using network 'development'
    Running 'ganache-cli -a 20'...
    Compiling contracts...
    Optimizer: Enabled   Runs: 200

    Running transfer.py - 1 test
     ✓ Deployment 'token' (0.1127s)
     ✓ Transfer tokens (0.1115s)

    Running approve_transferFrom.py - 3 tests
     ✓ Deployment 'token' (0.0783s)
     ✓ Set approval (0.1504s)
     ✓ Transfer tokens with transferFrom (0.1158s)
     ✓ transerFrom should revert (0.0441s)

    SUCCESS: All tests passed.

You can create as many test scripts as needed. Here is an example test script from the token project, `tests/transfer.py <https://github.com/brownie-mix/token-mix/blob/master/tests/transfer.py>`__:

.. code-block:: python
    :linenos:

    from brownie import *
    import scripts.token

    def setup():
        scripts.token.main()

    def transfer():
        '''Transfer tokens'''
        token = Token[0]
        check.equal(token.totalSupply(), "1000 ether", "totalSupply is wrong")
        token.transfer(accounts[1], "0.1 ether", {'from': accounts[0]})
        check.equal(
            token.balanceOf(accounts[1]),
            "0.1 ether",
            "Accounts 1 balance is wrong"
        )
        check.equal(
            token.balanceOf(accounts[0]),
            "999.9 ether",
            "Accounts 0 balance is wrong"
        )
