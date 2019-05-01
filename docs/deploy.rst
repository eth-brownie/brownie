.. _deploy:

===================
Deploying Contracts
===================

Along with the console, you can interact with your project by writing Python scripts. Scriping is especially useful for deploying contracts and automating common processes.

Every script must begin with ``from brownie import *``. This imports the instantiated project classes into the local namespace and gives access to the full Brownie :ref:`api`.

To execute a script from the command line:

::

    $ brownie run <script> [function]

From the console you can use the ``run`` method:

.. code-block:: python

    >>> run('token') # executes the main() function within scripts/token.py

Or the import statement:

.. code-block:: python

    >>> from scripts.token import main
    >>> main()

Scripts are stored in the ``scripts/`` folder. Each script can contain as many functions as you'd like. If no function name is given, brownie will attempt to run ``main``.

Here is a simple example script from the ``token`` project, used to deploy the ``Token`` contract from ``contracts/Token.sol`` using ``web3.eth.accounts[0]``.

.. code-block:: python
    :linenos:

    from brownie import *

    def main():
        accounts[0].deploy(Token, "Test Token", "TEST", 18, "1000 ether")

See the :ref:`api` documentation for available classes and methods when writing scripts.
