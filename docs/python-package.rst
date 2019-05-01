===========================
Brownie as a Python Package
===========================

Brownie can be imported as a package and used within regular Python scripts. This can be useful if you only require a specific function, or you would like more granular control over how Brownie operates.

For quick reference, the following three statements will give you an environment and namespace that is identical to what you have when loading the Brownie console:

.. code-block:: python

    from brownie import *
    project.load('path/to/your/project')
    rpc.launch()

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

The ``brownie.network`` module contains methods for network interaction.

.. code-block:: python

    >>> from brownie import network

Use ``brownie.network.rpc`` to launch a local RPC client such as ``ganache-cli``. Brownie will automatically connect to it.

.. code-block:: python

    >>> from brownie.network import rpc
    >>> rpc.launch()

Alternatively, if you are connecting to a remote RPC use ``network.connect``. The address to connect to is set in the configuration file.

.. code-block:: python

    >>> network.connect('ropsten')

Once connected, the ``accounts`` container will automatically populate with local accounts.

.. code-block:: python

    >>> from brownie.network import accounts
    >>> len(accounts)
    0
    >>> rpc.launch()
    >>> len(accounts)
    10

