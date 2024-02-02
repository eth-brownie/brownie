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
    ['Contract', 'Fixed', 'Wei', 'accounts', 'alert', 'compile_source', 'config', 'history', 'network', 'project', 'rpc', 'run', 'web3']

``brownie.exceptions``
======================

The ``exceptions`` module contains all Brownie :class:`Exception` and :class:`Warning` classes.

Exceptions
----------

.. py:exception:: brownie.exceptions.CompilerError

    Raised by the compiler when there is an error within a contract's source code.

.. py:exception:: brownie.exceptions.ContractExists

    Raised when attempting to create a new :func:`Contract <brownie.network.contract.Contract>` object, when one already exists for the given address.

.. py:exception:: brownie.exceptions.ContractNotFound

    Raised when attempting to access a :func:`Contract <brownie.network.contract.Contract>` object that no longer exists because the local network was reverted.

.. py:exception:: brownie.exceptions.EventLookupError

    Raised during lookup errors by :func:`EventDict <brownie.network.event.EventDict>` and :func:`_EventItem <brownie.network.event._EventItem>`.

.. py:exception:: brownie.exceptions.IncompatibleEVMVersion

    Raised when attempting to deploy a contract that was compiled to target an EVM version that is imcompatible than the currently active local RPC client.

.. py:exception:: brownie.exceptions.IncompatibleSolcVersion

    Raised when a project requires a version of solc that is not installed or not supported by Brownie.

.. py:exception:: brownie.exceptions.MainnetUndefined

    Raised when an action requires interacting with the main-net, but no ``"mainnet"`` network is defined.

.. py:exception:: brownie.exceptions.NamespaceCollision

    Raised by :func:`Sources <brownie.project.sources.Sources>` when the multiple source files contain a contract with the same name.

.. py:exception:: brownie.exceptions.PragmaError

    Raised when a contract has no pragma directive, or a pragma which requires a version of solc that cannot be installed.

.. py:exception:: brownie.exceptions.ProjectAlreadyLoaded

    Raised by :func:`project.load <main.load>` if a project has already been loaded.

.. py:exception:: brownie.exceptions.ProjectNotFound

    Raised by :func:`project.load <main.load>` when a project cannot be found at the given path.

.. py:exception:: brownie.exceptions.UndeployedLibrary

    Raised when attempting to deploy a contract that requires an unlinked library, but the library has not yet been deployed.

.. py:exception:: brownie.exceptions.UnknownAccount

    Raised when the :func:`Accounts <brownie.network.account.Accounts>` container cannot locate a specified :func:`Account <brownie.network.account.Account>` object.

.. py:exception:: brownie.exceptions.UnsetENSName

    Raised when an ENS name is unset (resolves to ``0x00``).

.. py:exception:: brownie.exceptions.UnsupportedLanguage

    Raised when attempting to compile a language that Brownie does not support.

.. py:exception:: brownie.exceptions.RPCConnectionError

    Raised when the RPC process is active and :func:`web3 <brownie.network.web3.Web3>` is connected, but Brownie is unable to communicate with it.

.. py:exception:: brownie.exceptions.RPCProcessError

    Raised when the RPC process fails to launch successfully.

.. py:exception:: brownie.exceptions.RPCRequestError

    Raised when a direct request to the RPC client has failed, such as a snapshot or advancing the time.

.. py:exception:: brownie.exceptions.VirtualMachineError

    Raised when a contract call causes the EVM to revert.

Warnings
--------

.. py:exception:: brownie.exceptions.BrownieCompilerWarning

    Raised by :func:`Contract.from_explorer <Contract.from_explorer>` when a contract cannot be compiled, or compiles successfully but produces unexpected bytecode.

.. py:exception:: brownie.exceptions.BrownieEnvironmentWarning

    Raised on unexpected environment conditions.

.. py:exception:: brownie.exceptions.InvalidArgumentWarning

    Raised on non-critical, invalid arguments passed to a method, function or config file.

``brownie._config``
===================

The ``_config`` module handles all Brownie configuration settings. It is not designed to be accessed directly. If you wish to view or modify config settings while Brownie is running, import ``brownie.config`` which will return a :func:`ConfigDict <brownie._config.ConfigDict>` with the active settings:

.. code-block:: python

    >>> from brownie import config
    >>> type(config)
    <class 'brownie._config.ConfigDict'>
    >>> config['network_defaults']
    {'name': 'development', 'gas_limit': False, 'gas_price': False}

ConfigDict
----------

.. py:class:: brownie._config.ConfigDict

    Subclass of :class:`dict` that prevents adding new keys when locked. Used to hold config file settings.

    .. code-block:: python

        >>> from brownie.types import ConfigDict
        >>> s = ConfigDict({'test': 123})
        >>> s
        {'test': 123}

ConfigDict Internal Methods
***************************

.. py:classmethod:: ConfigDict._lock

    Locks the :func:`ConfigDict <brownie._config.ConfigDict>`. When locked, attempts to add a new key will raise a :class:`KeyError`.

    .. code-block:: python

        >>> s._lock()
        >>> s['other'] = True
        Traceback (most recent call last):
          File "<console>", line 1, in <module>
        KeyError: 'other is not a known config setting'

.. py:classmethod:: ConfigDict._unlock

    Unlocks the :func:`ConfigDict <brownie._config.ConfigDict>`. When unlocked, new keys can be added.

    .. code-block:: python

        >>> s._unlock()
        >>> s['other'] = True
        >>> s
        {'test': 123, 'other': True}

.. py:classmethod:: ConfigDict._copy

    Returns a copy of the object as a :class:`dict`.

``brownie._singleton``
======================

.. py:class:: brownie._singleton._Singleton

Internal metaclass used to create `singleton <https://en.wikipedia.org/wiki/Singleton_pattern>`_ objects. Instantiating a class derived from this metaclass will always return the same instance, regardless of how the child class was imported.
