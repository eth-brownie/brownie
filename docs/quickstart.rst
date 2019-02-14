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

* ``build/``: Directory for compiled contracts and network data
* ``contracts/``: Directory for solidity contracts
* ``scripts/``: Directory for any scripts that are not tests
* ``tests/``: Directory for test scripts
* ``brownie-config.json``: Configuration file for the project

You can also initialize already existing projects. For the purposes of this document, we will use the ``token`` project, which is a very basic ERC-20 implementation:

::

    $ brownie init token

This will create a new folder ``token/`` and deploy the project inside it.

Interacting with your Project
=============================

The brownie console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop. It feels similar to a python interpreter. To open it:

::

    $ brownie console

Brownie will compile your contracts, start the local RPC, and then give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`. You can use builtins ``dir`` and ``help`` for quick reference to available methods and attributes.

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
    <ContractConstructor object 'Token.constructor(string,string,uint256,uint256)'>
    >>> t = Token.deploy(accounts[1], "Test Token", "TST", 18, "1000 ether")

    Transaction sent: 0x2e3cab83342edda14141714ced002e1326ecd8cded4cd0cf14b2f037b690b976
    Transaction confirmed - block: 1   gas spent: 594186
    Contract deployed at: 0x5419710735c2D6c3e4db8F30EF2d361F70a4b380
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>>
    >>> t
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>
    >>> Token
    [<Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>]
    >>> Token[0]
    <Token Contract object '0x5419710735c2D6c3e4db8F30EF2d361F70a4b380'>


Running Scripts
===============

You can write scripts to automate contract deployment and interaction:

::

    $ brownie run

If you look at the token project, you will find an example one at ``scripts/token.py``:

.. literalinclude:: ../projects/token/scripts/token.py
    :linenos:
    :language: python
    :lines: 3-

Calling the ``deploy`` method deploys the ``Token`` contract from ``contracts/Token.sol`` using ``web3.eth.accounts[0]``.

Testing a Project
=================

To run all of the test scripts in ``tests/``:

::

    $ brownie test

Running it in the token project, you will receive output similar to the following:

::

    $ brownie test
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

You can create as many test scripts as needed. Here is an example test script from the token project, ``tests/transfer.py``:

.. literalinclude:: ../projects/token/tests/transfer.py
    :linenos:
    :language: python
    :lines: 3-
