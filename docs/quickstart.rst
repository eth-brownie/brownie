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
* ``deployments/``: Directory for deployment scripts
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

Using The Console
=================

The console feels similar to a python interpreter. It is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop. To open it:

::

    $ brownie console

Brownie will compile your contracts, start the local RPC, and then give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`.
