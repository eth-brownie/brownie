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

Unlinked Libraries
==================

If a contract requires a library, the most recently deployed one will be used automatically. If the required library has not been deployed yet an ``UndeployedLibrary`` exception is raised.

.. code-block:: python

    >>> accounts[0].deploy(MetaCoin)
      File "brownie/network/contract.py", line 167, in __call__
        f"Contract requires '{library}' library but it has not been deployed yet"
    UndeployedLibrary: Contract requires 'ConvertLib' library but it has not been deployed yet

    >>> accounts[0].deploy(ConvertLib)
    Transaction sent: 0xff3f5cff35c68a73658ad367850b6fa34783b4d59026520bd61b72b6613d871c
    ConvertLib.constructor confirmed - block: 1   gas used: 95101 (48.74%)
    ConvertLib deployed at: 0x08c4C7F19200d5636A1665f6048105b0686DFf01
    <ConvertLib Contract object '0x08c4C7F19200d5636A1665f6048105b0686DFf01'>

    >>> accounts[0].deploy(MetaCoin)
    Transaction sent: 0xd0969b36819337fc3bac27194c1ff0294dd65da8f57c729b5efd7d256b9ecfb3
    MetaCoin.constructor confirmed - block: 2   gas used: 231857 (69.87%)
    MetaCoin deployed at: 0x8954d0c17F3056A6C98c7A6056C63aBFD3e8FA6f
    <MetaCoin Contract object '0x8954d0c17F3056A6C98c7A6056C63aBFD3e8FA6f'>
