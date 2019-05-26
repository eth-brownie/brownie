.. _api-project:

===========
Project API
===========

The ``project`` package contains classes and methods for initializing, loading and compiling Brownie projects.

At startup, Brownie automatically loads your project and creates objects to interact with it. It is unlikely you will need to use this package unless you are using Brownie via the regular python interpreter.

``brownie.project.loader``
==========================

The ``loader`` module contains methods for creating, loading, and closing projects. All of these methods are available directly from ``brownie.project``.

Package Methods
---------------

.. py:method:: loader.check_for_project(path)

    Checks for an existing Brownie project within a folder and it's parent folders, and returns the base path to the project as a ``Path`` object.  Returns ``None`` if no project is found.

    .. code-block:: python

        >>> from brownie import project
        >>> Path('.').resolve()
        PosixPath('/my_projects/token/build/contracts')
        >>> project.check_for_project('.')
        PosixPath('/my_projects/token')


.. py:method:: loader.new(project_path=".", ignore_subfolder=False)

    Initializes a new project at the given path.  If the folder does not exist, it will be created.

    Returns the path to the project as a string.

    .. code-block:: python

        >>> from brownie import project
        >>> project.new('/my_projects/new_project')
        PosixPath('/my_projects/new_project')

.. py:method:: loader.load(project_path=None)

    Loads a Brownie project and creates ``ContractContainer`` objects. If no path is given, attempts to find one using ``check_for_project('.')``.

    Instantiated objects will be available from within the ``project`` module after this call.  If Brownie was previously imported via ``from brownie import *``, they will also be available in the local namespace.

    Returns a list of ``ContractContainer`` objects.

    .. code-block:: python

        >>> from brownie import project
        >>> project.load('/my_projects/token')
        [<ContractContainer object 'Token'>, <ContractContainer object 'SafeMath'>]
        >>> project.Token
        <ContractContainer object 'Token'>

.. py:method:: loader.close(raises=True)

    Closes the active Brownie project and removes the ``ContractContainer`` instances from the namespace.

    .. code-block:: python

        >>> from brownie import project
        >>> project.close()

.. py:method:: loader.compile_source(source)

    Compiles the given Solidity source code string and returns a list of ``ContractContainer`` objects. The containers are **not** added to the global or project namespaces.

    Raises ``brownie.exceptions.ContractExists`` if any contracts in the source code use the same name as a contract in the active project.

    .. code-block:: python

        >>> from brownie import compile_source
        >>> container = compile_source('''pragma solidity 0.4.25;

        contract SimpleTest {

          string public name;

          constructor (string _name) public {
            name = _name;
          }
        }'''
        >>>
        >>> container
        [<ContractContainer object 'SimpleTest'>]

.. _api-project-build:

``brownie.project.build``
=========================

The ``build`` module contains methods used internally by Brownie to interact with files in a project's ``build/contracts`` folder.

Module Methods
--------------

.. py:method:: build.load(project_path)

    Loads all build files for the given project path. Files that are corrupted or missing required keys will be deleted.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.load('/my_projects/token')

.. py:method:: build.add(build_json)

    Adds a build json to the active project. The data is saved in the ``build/contracts`` folder.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.add(build_json)

.. py:method:: build.delete(contract_name)

    Removes a contract's build data from the active project.  The json file in ``build/contracts`` is deleted.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.delete('Token')

.. py:method:: build.clear()

    Clears all currently available build data.  No files are deleted.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.clear()

.. py:method:: build.get(contract_name)

    Returns build data for the given contract name.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.get('Token')
        {...}

.. py:method:: build.items(path=None)

    Provides an list of tuples in the format ``('contract_name', build_json)``, similar to calling ``dict.items``.  If a path is given, only contracts derived from that source file are returned.

    .. code-block:: python

        >>> from brownie.project import build
        >>> for name, data in build.items():
        ...     print(name)
        Token
        SafeMath

.. py:method:: build.contains(contract_name)

    Checks if a contract with the given name is in the currently loaded build data.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.contains('Token')
        True

.. py:method:: build.get_dependents(contract_name)

    Returns a list of contract names that the given contract inherits from or links to. Used by the compiler when determining which contracts to recompile based on a changed source file.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.get_dependents('Token')
        ['SafeMath']

.. py:method:: build.get_dev_revert(pc)

    Given the program counter from a stack trace that caused a transaction to revert, returns the :ref:`commented dev string <dev-revert>` (if any). Used by ``TransactionReceipt``.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.get_dev_revert(1847)
        "dev: zero value"

.. py:method:: build.get_error_source_from_pc(pc)

    Given the program counter from a stack trace that caused a transaction to revert, returns the highlighted relevent source code.  Used by ``TransactionReceipt`` when generating a ``VirtualMachineError``.

``brownie.project.compiler``
============================

The ``compiler`` module contains methods for compiling contracts and formatting the compiled data. This module is used internally whenever a Brownie project is loaded.

In most cases you will not wish to call methods in this module directly. Instead you should use ``project.load`` to compile your project initially and ``project.compile_source`` for adding individual, temporary contracts.

Module Methods
--------------

.. py:method:: compiler.set_solc_version()

    Sets the ``solc`` version based on the configuration settings for the active project.

.. py:method:: compiler.compile_contracts(contracts, silent=False)

    Given a dict in the format ``{'path': "source code"}``, compiles the contracts and returns the build data.  See :ref:`compile-json`.

.. py:method:: compiler.compile_source(source)

    Given a string of contract source code, compiles it and returns a dict of compiled data.

    It is usually preferred to call ``project.compile_source``, which calls this method under the hood, adds the returned data to ``project.build``, and returns ``ContractContainer`` objects.

``brownie.project.sources``
===========================

The ``sources`` module contains methods to access project source code files and information about them.

Module Methods
--------------

.. py:classmethod:: sources.get(name)

    Returns the source code file for the given name. ``name`` can be a path or a contract name.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get('SafeMath')
        "pragma solidity ^0.5.0; ..."

.. py:classmethod:: sources.get_path_list()

    Returns a list of contract source paths for the active project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_path_list()
        ['contracts/Token.sol', 'contracts/SafeMath.sol']

.. py:classmethod:: sources.get_contract_list()

    Returns a list of contract names for the active project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_contract_list()
        ['Token', 'SafeMath']

.. py:classmethod:: sources.load(project_path)

    Loads all source files for the given project path. Raises ``ContractExists`` if two source files contain contracts with the same name.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.load('my_projects/token')

.. py:classmethod:: sources.clear()

    Clears all currently loaded source files.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.clear()

.. py:classmethod:: sources.remove_comments(source)

    Given contract source as a string, returns the same contract with all the comments removed.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> token_source = sources.get('Token')
        >>> source.remove_comments(token_source)
        "pragma solidity ^0.5.0; ..."

.. py:classmethod:: sources.compile_paths(paths)

    Compiles a list of contracts given in ``paths``. The contract sources must have already been loaded via ``sources.load``.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.compile_paths(['contracts/Token.sol'])

.. py:classmethod:: sources.compile_source(source)

    Compiles source code given as a string and adds it to the available sources. The path will be set to ``<string-X>`` where X is an integer staring at one.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> source.compile_source('...')

.. py:classmethod:: sources.get_hash(contract_name)

    Returns a hash of the contract source code.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_hash('Token')
        'da39a3ee5e6b4b0d3255bfef95601890afd80709'

.. py:classmethod:: sources.get_source_path(contract_name)

    Returns the path to the file where a contract is located.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_source_path('Token')
        'contracts/Token.sol'

.. py:classmethod:: sources.get_fn(contract, offset)

    Given a contract name, start and stop offset, returns the name of the associated function. Returns ``False`` if the offset spans multiple functions.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_fn("Token", (2000, 2020))
        'Token.balanceOf'

.. py:classmethod:: sources.get_fn_offset(contract, fn_name)

    Given a contract and function name, returns the source offsets of the function.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_fn_offset("Token", "balanceOf")
        (1992, 2050)

.. py:classmethod:: sources.get_contract_name(path, offset)

    Given a path and source offsets, returns the name of the contract. Returns ``False`` if the offset spans multiple contracts.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_contract_name("contracts/Token.sol", (1000, 1200))
        "Token"

.. py:classmethod: sources.get_highlighted_source(path, offset, pad=3)

    Given a path, start and stop offset, returns highlighted source code. Called internally by ``TransactionReceipt.source``.

.. py:classmethod:: sources.is_inside_offset(inner, outer)

    Returns a boolean indicating if the first offset is contained completely within the second offset.
