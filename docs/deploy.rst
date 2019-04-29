.. _deploy:

===================
Deploying Contracts
===================

Scripts are useful for deploying contracts or interacting with your project on the testnet or mainnet. To run a script from the command line:

::

    $ brownie run <script> [function]

In the console you can use run:

::

    >>> run('token') # executes the main() function within scripts/token.py

or the import statement:

::

    >>> import scripts.token # imports scripts/token.py

Scripts are stored in the ``scripts/`` folder. Each script can contain as many functions as you'd like. If no function name is given, brownie will attempt to run ``main``.

Every script must begin with ``from brownie import *`` in order to give access to the :ref:`api`.

Here is a simple example script from the ``token`` project, used to deploy the ``Token`` contract from ``contracts/Token.sol`` using ``web3.eth.accounts[0]``.

.. literalinclude:: ../projects/token/scripts/token.py
    :linenos:
    :language: python
    :lines: 3-

See the :ref:`api` documentation for available classes and methods when writing scripts.
