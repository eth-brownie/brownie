.. _scripts:

=======================
Writing Brownie Scripts
=======================

Along with the console, you can write scripts for quick testing or to automate common processes. Scripting is also useful when deploying your contracts to a non-local network.

Scripts are stored in the ``scripts/`` directory within your project.

Layout of a Script
==================

Brownie scripts use standard Python syntax, but there are a few things to keep in mind in order for them to execute properly.

Import Statements
-----------------

Unlike the console where all of Brownie's objects are already available, in a script you must first import them. The simplest way to do this is via a wildcard import:

.. code-block:: python

    from brownie import *

This imports the instantiated project classes into the local namespace and gives access to the :ref:`Brownie API <api>` in exactly the same way as if you were using the console.

Alternatively you may wish to only import exactly the classes and methods required by the script. For example:

.. code-block:: python

    from brownie import Token, accounts

This makes available the ``accounts`` and ``Token`` containers, which is enough to deploy a contract.

Functions
---------

Each script can contain as many functions as you'd like. When executing a script, brownie attempts to run the ``main`` function if no other function name is given.

Running Scripts
===============

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
========

Here is a simple example script from the ``token`` project, used to deploy the ``Token`` contract from ``contracts/Token.sol`` using ``web3.eth.accounts[0]``.

.. code-block:: python
    :linenos:

    from brownie import Token, accounts

    def main():
        accounts[0].deploy(Token, "Test Token", "TEST", 18, "1000 ether")

And here is an expanded version of the same script, that includes a simple method for distributing tokens.

.. code-block:: python
    :linenos:

    from brownie import Token, accounts

    def main():
        token = accounts[0].deploy(Token, "Test Token", "TEST", 18, "1000 ether")
        return token

    def distribute_tokens(sender=accounts[0], receiver_list=accounts[1:]):
        token = main()
        for receiver in receiver_list:
            token.transfer(receiver, "1 ether", {'from': sender})
