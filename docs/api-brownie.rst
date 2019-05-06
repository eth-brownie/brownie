.. _api-brownie:

===========
Brownie API
===========

``brownie``
===========

The ``brownie`` package is the main package containing all of Brownie's functionality.

.. code-block:: python

    >>> from brownie import *
    >>> dir()
    ['Gui', 'accounts', 'alert', 'brownie', 'check', 'compile_source', 'config', 'history', 'network', 'project', 'rpc', 'web3', 'wei']

``brownie.exceptions``
======================

The ``exceptions`` module contains all Brownie ``Exception`` classes.

.. py:exception:: CompilerError

    Raised by the compiler when there is an error within a contract's source code.

.. py:exception:: ExpectedFailing

    Raised when a unit test is marked as ``pending=True`` but it still passes.

.. py:exception:: RPCConnectionError

    Raised when the RPC process is active and ``web3`` is connected, but Brownie is unable to communicate with it.

.. py:exception:: RPCProcessError

    Raised when the RPC process fails to launch successfully.

.. py:exception:: VirtualMachineError

    Raised when a call to the EVM reverts.

``brownie._config``
===================

The ``_config`` module handles all Brownie configuration settings. It is not designed to be accessed directly. If you wish to view or modify config settings while brownie is running, import ``brownie.config`` which will return a :ref:`api-types-strictdict` that contains all the settings:

.. code-block:: python

    >>> from brownie import config
    >>> type(config)
    <class 'brownie.types.types.StrictDict'>
    >>> config['network_defaults']
    {'name': 'development', 'gas_limit': False, 'gas_price': False}
