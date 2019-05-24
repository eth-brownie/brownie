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

network
*******

.. py:exception:: brownie.exceptions.UnknownAccount

    Raised when the ``Accounts`` container cannot locate a specified ``Account`` object.

.. py:exception:: brownie.exceptions.AmbiguousMethods

    Raised by ``ContractContainer`` when a contract has multiple methods that share the same name.

.. py:exception:: brownie.exceptions.UndeployedLibrary

    Raised when attempting to deploy a contract that requires an unlinked library, but the library has not yet been deployed.

.. py:exception:: brownie.exceptions.RPCConnectionError

    Raised when the RPC process is active and ``web3`` is connected, but Brownie is unable to communicate with it.

.. py:exception:: brownie.exceptions.RPCProcessError

    Raised when the RPC process fails to launch successfully.

.. py:exception:: brownie.exceptions.RPCRequestError

    Raised when a direct request to the RPC client has failed, such as a snapshot or advancing the time.

.. py:exception:: brownie.exceptions.VirtualMachineError

    Raised when a contract call causes the EVM to revert.

project
*******

.. py:exception:: brownie.exceptions.ContractExists

    Raised by ``project.compile_source`` when the source code contains a contract with a name that is the same as a contract in the active project.

.. py:exception:: brownie.exceptions.ProjectAlreadyLoaded

    Raised by ``project.load_project`` if a project has already been loaded.

.. py:exception:: brownie.exceptions.ProjectNotFound

    Raised by ``project.load_project`` when a project cannot be found at the given path.

.. py:exception:: brownie.exceptions.CompilerError

    Raised by the compiler when there is an error within a contract's source code.

test
****

.. py:exception:: brownie.exceptions.ExpectedFailing

    Raised when a unit test is marked as ``pending=True`` but it still passes.

types
*****

.. py:exception:: brownie.exceptions.InvalidABI

    Raised when an invalid ABI is given while converting contract inputs or outputs.



``brownie._config``
===================

The ``_config`` module handles all Brownie configuration settings. It is not designed to be accessed directly. If you wish to view or modify config settings while brownie is running, import ``brownie.config`` which will return a :ref:`api-types-strictdict` that contains all the settings:

.. code-block:: python

    >>> from brownie import config
    >>> type(config)
    <class 'brownie.types.types.StrictDict'>
    >>> config['network_defaults']
    {'name': 'development', 'gas_limit': False, 'gas_price': False}
