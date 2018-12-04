.. _quickstart:

==========
Quickstart
==========

This page will walk you through the basics of using Brownie. Please review the rest of the documentation to learn more about specific functionality.

.. note:: This project relies heavily upon Web3.py. This documentation assumes a basic familiarity with it. You may wish to view the `Web3.py docs <https://web3py.readthedocs.io/en/stable/index.html>`__ if you have not used it previously.

Initializing a New Project
==========================

The first step to using Brownie is to initialize a new project. To do this, create a new empty folder and then type:

::

    $ brownie init

This will create the following project structure within the folder:

* ``contracts/``: Directory for solidity contracts
* ``deployments/``: Directory for deployment scripts
* ``environments/``: Directory for persistent environment data files
* ``test/``: Directory for test scripts
* ``brownie-config.json``: Configuration file for the project

You can also initialize already existing projects. For the purposes of this document, we will use the ``token`` project, which is a very basic ERC-20 implementation:

::

    $ brownie init token

This will create a new folder ``token/`` and deploy the project inside it.


Deploying a Project
===================

The simplest way to deploy a project is to run a deployment script:

::

    $ brownie deploy

If you look at the token project, you will find an example one at ``deployments/token.py``:

.. literalinclude:: ../projects/token/deployments/token.py
    :linenos:
    :language: python
    :lines: 3-

This deploys the ``Token`` contract from ``contracts/Token.sol`` using ``web3.eth.accounts[0]``.

Testing a Project
=================

To run all of the test scripts in ``test/``:

::

    $ brownie test

Running it in the token project, you will receive output similar to the following:

::

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

Using The Console
=================

The console works similarly to a normal python interpreter. You can use it to directly interact with your project:

::

    $ brownie console
    Using network 'development'
    Running 'ganache-cli -a 20'...
    Compiling contracts...
    Optimizer: Enabled   Runs: 200
    Brownie environment is ready.
    >>>

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

