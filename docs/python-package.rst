===========================
Brownie as a Python Package
===========================

Brownie can be imported as a package and used within regular Python scripts. This can be useful if you only require a specific function, or you would like more granular control over how Brownie operates.

For quick reference, the following three statements will give you an environment and namespace that is identical to what you have when loading the Brownie console:

.. code-block:: python

    from brownie import *
    project.load('path/to/your/project')
    network.conect('development')

Loading a Project
=================

The ``brownie.project`` module is used to load a Brownie project.

.. code-block:: python

    >>> import brownie.project as project
    >>> project.load('myprojects/token')
    [<ContractContainer object 'Token'>, <ContractContainer object 'SafeMath'>]

Once loaded, the contract instances are available within ``project``.

.. code-block:: python

    >>> project.Token
    <ContractContainer object 'Token'>

Alternatively, use a ``from .. import *`` style command to import ``brownie`` or ``brownie.project`` and the classes will be available in the local namespace.

.. code-block:: python

    >>> from brownie import *
    >>> project.load('myprojects/token')
    [<ContractContainer object 'Token'>, <ContractContainer object 'SafeMath'>]
    >>> Token
    <ContractContainer object 'Token'>

Accessing the Network
=====================

The ``brownie.network`` module contains methods for network interaction. The simplest way to connect is with the ``network.connect`` method:

.. code-block:: python

    >>> from brownie import network
    >>> network.connect('development')

This method queries the network settings from the configuration file, launches the local RPC, and connects to it with a ``Web3`` instance. Alternatively, you can accomplish the same with these commands:

.. code-block:: python

    >>> from brownie.network import rpc, web3
    >>> rpc.launch('ganache-cli')
    >>> web3.connect('http://127.0.0.1:8545')

Once connected, the ``accounts`` container will automatically populate with local accounts.

.. code-block:: python

    >>> from brownie.network import accounts
    >>> len(accounts)
    0
    >>> network.connect('development')
    >>> len(accounts)
    10
