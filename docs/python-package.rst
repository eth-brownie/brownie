===========================
Brownie as a Python Package
===========================

Brownie can be imported as a package and used within regular Python scripts. This can be useful if you wish to incorporate a specific function or range of functionality within a greater project, or if you would like more granular control over how Brownie operates.

For quick reference, the following statements generate an environment and namespace identical to what you have when loading the Brownie console:

.. code-block:: python

    from brownie import *
    project.load('my_projects/token', name="TokenProject")
    from brownie.project.TokenProject import *
    network.conect('development')

Loading a Project
=================

The ``brownie.project`` module is used to load a Brownie project.

.. code-block:: python

    >>> import brownie.project as project
    >>> project.load('myprojects/token')
    <Project object 'TokenProject'>

Once loaded, the ``Project`` object is available within ``brownie.project``. This container holds all of the related ``ContractContainer`` objects.

.. code-block:: python

    >>> p = project.TokenProject
    >>> p
    <Project object 'TokenProject'>
    >>> p.Token
    <ContractContainer object 'Token'>

Alternatively, use a ``from`` import statement to import ``ContractContainer`` objects to the local namespace:

.. code-block:: python

    >>> from brownie.project.TokenProject import Token
    >>> Token
    <ContractContainer object 'Token'>

 Importing with a wildcard will retrieve every available ``ContractContainer``:

.. code-block:: python

    >>> from brownie.project.TokenProject import *
    >>> Token
    <ContractContainer object 'Token'>
    >>> SafeMath
    <ContractContainer object 'SafeMath'>

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

Once connected, the ``accounts`` container is automatically populated with local accounts.

.. code-block:: python

    >>> from brownie.network import accounts
    >>> len(accounts)
    0
    >>> network.connect('development')
    >>> len(accounts)
    10
