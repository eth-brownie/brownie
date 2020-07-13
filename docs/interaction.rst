.. _interaction:

===============================
Interacting with your Contracts
===============================

Brownie has three main components that you can use while developing your project:

    1. The :ref:`console<console>` is useful for quick testing and debugging.
    2. :ref:`Scripts<scripts>` allow you to automate common tasks and handle deployments.
    3. :ref:`Tests<tests-intro>` help to ensure that your contracts are executing as intended.

.. _console:

Using the Console
=================

The console is useful when you want to interact directly with contracts deployed on a non-local chain, or for quick testing as you develop. It's also a great starting point to familiarize yourself with Brownie's functionality.

The console feels very similar to a regular python interpreter. From inside a project directory, load it by typing:

::

    $ brownie console

Brownie will compile the contracts, launch or attach to the local test environment, and then give you a command prompt. From here you may interact with the network with the full range of functionality offered by the :ref:`api`.

.. hint::

    You can call the builtin :func:`dir <dir>` method to see available methods and attributes for any class. Classes, methods and attributes are highlighted in different colors.

    You can also call :func:`help <help>` on any class or method to view information on it's functionality.

.. _scripts:

Writing Scripts
===============

Along with the console, you can write scripts for quick testing or to automate common processes. Scripting is also useful when deploying your contracts to a non-local network.

Scripts are stored in the ``scripts/`` directory within your project.

Layout of a Script
------------------

Brownie scripts use standard Python syntax, but there are a few things to keep in mind in order for them to execute properly.

Import Statements
*****************

Unlike the console where all of Brownie's objects are already available, in a script you must first import them. The simplest way to do this is via a wildcard import:

.. code-block:: python

    from brownie import *

This imports the instantiated project classes into the local namespace and gives access to the :ref:`Brownie API <api>` in exactly the same way as if you were using the console.

Alternatively you may wish to only import exactly the classes and methods required by the script. For example:

.. code-block:: python

    from brownie import Token, accounts

This makes available the :func:`accounts <brownie.network.account.Accounts>` and :func:`Token <brownie.network.contract.ContractContainer>` containers, which is enough to deploy a contract.

Functions
*********

Each script can contain as many functions as you'd like. When executing a script, brownie attempts to run the ``main`` function if no other function name is given.

Running Scripts
---------------

To execute a script from the command line:

::

    $ brownie run <script> [function]

From the console, you can use the ``run`` method:

.. code-block:: python

    >>> run('token') # executes the main() function within scripts/token.py

You can also import and call the script directly:

.. code-block:: python

    >>> from scripts.token import main
    >>> main()

Examples
--------

Here is a simple example script from the ``token`` project, used to deploy the ``Token`` contract from ``contracts/Token.sol`` using ``web3.eth.accounts[0]``.

.. code-block:: python
    :linenos:

    from brownie import Token, accounts

    def main():
        Token.deploy("Test Token", "TST", 18, 1e23, {'from': accounts[0]})

And here is an expanded version of the same script, that includes a simple method for distributing tokens.

.. code-block:: python
    :linenos:

    from brownie import Token, accounts

    def main():
        token = Token.deploy("Test Token", "TST", 18, 1e23, {'from': accounts[0]})
        return token

    def distribute_tokens(sender=accounts[0], receiver_list=accounts[1:]):
        token = main()
        for receiver in receiver_list:
            token.transfer(receiver, 1e18, {'from': sender})

.. _tests-intro:

Writing Tests
=============

Brownie leverages ``pytest`` and ``hypothesis`` to provide a robust framework for testing your contracts.

Test scripts are stored in the ``tests/`` directory of your project. To run the complete test suite:

::

    $ brownie test

To learn more about writing tests in Brownie, you should start by reviewing the :ref:`Brownie Pytest documentation<pytest>`.
