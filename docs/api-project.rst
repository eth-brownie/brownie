.. _api-project:

===========
Project API
===========

``brownie.project``
===================

The ``project`` package contains classes and methods for initializing, loading and compiling Brownie projects.

Package Methods
---------------

.. py:method:: project.check_for_project(path)

    Checks for an existing Brownie project within a folder and it's parent folders, and returns the base path to the project as a ``Path`` object.  Returns ``None`` if no project is found.

    .. code-block:: python

        >>> from brownie.project import check_for_project
        >>> Path('.').resolve()
        PosixPath('/my_projects/token/build/contracts')
        >>> check_for_project('.')
        PosixPath('/my_projects/token')


.. py:method:: project.new(path=".", ignore_subfolder=False)

    Initializes a new project at the given path.  If the folder does not exist, it will be created.

    Returns the path to the project as a string.

    .. code-block:: python

        >>> from brownie import project
        >>> project.new('/my_projects/new_project')
        PosixPath('/my_projects/new_project')

.. py:method:: project.load(path=None)

    Loads a Brownie project and instantiates various related objects. If no path is given, attempts to find one using ``check_for_project('.')``.

    Instantiated objects will be available from within the ``project`` module after this call.  If Brownie was previously imported via ``from brownie import *``, they will also be available in the local namespace.

    Returns a list of ``ContractDeployer`` objects.

    .. code-block:: python

        >>> from brownie import project
        >>> project.load('/my_projects/token')
        [<ContractContainer object 'Token'>, <ContractContainer object 'SafeMath'>]
        >>> project.Token
        <ContractContainer object 'Token'>


.. py:method:: project.compile_source(source)

    Compiles the given Solidity source code string and returns a list of ContractContainer instances.

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


``brownie.project.build``
=========================

The ``build`` module contains classes and methods used internally by Brownie to interact with files in a project's ``build`` folder.

.. _api-project-build:

Build
-----

.. py:class:: build.Build()

    Dict-like :ref:`api-types-singleton` container. Used internally to access the build data in ``build/contracts``.

    .. code-block:: python

        >>> from brownie.project.build import Build
        >>> build = Build()
        >>> token_json = build["Token"]
        >>> token_json.keys()
        dict_keys(['abi', 'allSourcePaths', 'ast', 'bytecode', 'bytecodeSha1', 'compiler', 'contractName', 'coverageMap', 'deployedBytecode', 'deployedSourceMap', 'opcodes', 'pcMap', 'sha1', 'source', 'sourceMap', 'sourcePath', 'type'])

Module Methods
--------------

.. py:method:: build.get_ast_hash(script_path)

    Given the path of a python script, Generates a hash from it's `AST <https://docs.python.org/3/library/ast.html>`_ and each of it's local imports. This is used to check for changes when determining if unit tests need to be re-run.

    .. code-block:: python

        >>> from brownie.project.build import get_ast_hash
        >>> get_ast_hash('tests/transfer.py')
        e1a0a28ec557194e8f1e76db0604b75a5a070bb7

``brownie.project.compiler``
============================

The ``compiler`` module contains methods for compiling contracts and formatting the compiled data. This module is used internally whenever a Brownie project is loaded.

Module Methods
--------------

.. py:method:: compiler.set_solc_version()

    Sets the ``solc`` version based on the configuration settings for the active project.

.. py:method:: compiler.compile_contracts(contract_paths)

    Given a list of contract paths as strings or ``Path`` objects, compiles them and returns a dict of compiled data.  See :ref:`compile-json`.

.. py:method:: compiler.compile_source(source)

    Given a string of contract source code, compiles it and returns a dict of compiled data.

    It is usually preferred to call ``project.compile_source``, which calls this method under the hood and then instantiates a ``ContractContainer`` from the returned build data.

``brownie.project.sources``
===========================

The ``sources`` module contains the ``Sources`` class which is used to access project source code and information about it.

Sources
-------

.. py:class:: sources.Sources()

    Dict-like :ref:`api-types-singleton` container used internally to access source code for the project's contracts.

    .. code-block:: python

        >>> from brownie.project.sources import Sources
        >>> s = Sources()

.. py:classmethod:: Sources.remove_comments(path)

    Given the path to a contract source file, removes comments from the source code and returns it as a string.

.. py:classmethod:: Sources.get_hash(contract_name)

    Returns a hash of the contract source code. This hash is generated specifically from the given contract name (not the entire containing file), after comments have been removed.

.. py:classmethod:: Sources.get_path(contract_name)

    Returns the absolute path to the file where a contract is located.

.. py:classmethod:: Sources.get_type(contract_name)

    Returns the type of contract (contract, interface, library).

.. py:classmethod:: Sources.inheritance_map()

    Returns a set of all contracts that the given contract inherits from.

.. py:classmethod: Sources.add_source(source)

    Given source code as a string, adds it to the object and returns a path string formatted as ``<string-X>`` where X is a number that is incremented.
