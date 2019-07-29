.. _api-project:

===========
Project API
===========

The ``project`` package contains classes and methods for initializing, loading and compiling Brownie projects.

At startup Brownie automatically loads your project and creates objects to interact with it. It is unlikely you will need to use this package unless you are using Brownie via the regular python interpreter.

``brownie.project.main``
==========================

The ``main`` module contains higher level methods for creating, loading, and closing projects. All of these methods are available directly from ``brownie.project``.

Package Methods
---------------

.. py:method:: main.check_for_project(path)

    Checks for an existing Brownie project within a folder and it's parent folders, and returns the base path to the project as a ``Path`` object.  Returns ``None`` if no project is found.

    .. code-block:: python

        >>> from brownie import project
        >>> Path('.').resolve()
        PosixPath('/my_projects/token/build/contracts')
        >>> project.check_for_project('.')
        PosixPath('/my_projects/token')


.. py:method:: main.new(project_path=".", ignore_subfolder=False)

    Initializes a new project at the given path.  If the folder does not exist, it will be created.

    Returns the path to the project as a string.

    .. code-block:: python

        >>> from brownie import project
        >>> project.new('/my_projects/new_project')
        '/my_projects/new_project'

.. py:method:: main.pull(project_name, project_path=None, ignore_subfolder=False)

    Initializes a new project via a template. Templates are downloaded from the `Brownie Mix github repo <https://github.com/brownie-mix>`_.

    If no path is given, the project will be initialized in a subfolder of the same name.

    Returns the path to the project as a string.

    .. code-block:: python

        >>> from brownie import project
        >>> project.pull('token')
        Downloading from https://github.com/brownie-mix/token-mix/archive/master.zip...
        'my_projects/token'

.. py:method:: main.load(project_path=None)

    Loads a Brownie project and creates ``ContractContainer`` objects. If no path is given, attempts to find one using ``check_for_project('.')``.

    Instantiated objects will be available from within the ``project`` module after this call.  If Brownie was previously imported via ``from brownie import *``, they will also be available in the local namespace.

    Returns a list of ``ContractContainer`` objects.

    .. code-block:: python

        >>> from brownie import project
        >>> project.load('/my_projects/token')
        [<ContractContainer object 'Token'>, <ContractContainer object 'SafeMath'>]
        >>> project.Token
        <ContractContainer object 'Token'>

.. py:method:: main.close(raises=True)

    Closes the active Brownie project and removes the ``ContractContainer`` instances from the namespace.

    .. code-block:: python

        >>> from brownie import project
        >>> project.close()

.. py:method:: main.compile_source(source)

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

    Given the program counter from a stack trace that caused a transaction to revert, returns the highlighted relevent source code and the name of the method that reverted.

    Used by ``TransactionReceipt`` when generating a ``VirtualMachineError``.

.. py:method:: build.expand_build_offsets(build_json)

    Given a build json as a dict, expands the minified offsets to match the original source code.

``brownie.project.compiler``
============================

The ``compiler`` module contains methods for compiling contracts, and formatting the compiled data. This module is used internally whenever a Brownie project is loaded.

In most cases you will not wish to call methods in this module directly. Instead you should use ``project.load`` to compile your project initially and ``project.compile_source`` for adding individual, temporary contracts. Along with compiling, these methods also add the returned data to ``project.build`` and return ``ContractContainer`` objects.

Module Methods
--------------

.. py:method:: compiler.set_solc_version(version)

    Sets the ``solc`` version. If the requested version is not available it will be installed.

    .. code-block:: python

        >>> from brownie.project import compiler
        >>> compiler.set_solc_version("0.4.25")
        Using solc version v0.4.25


.. py:method:: compiler.install_solc(*versions)

    Installs one or more versions of ``solc``.

    .. code-block:: python

        >>> from brownie.project import compiler
        >>> compiler.install_solc("0.4.25", "0.5.10")

.. py:method:: compiler.compile_and_format(contracts, solc_version=None, optimize=True, runs=200, evm_version=None, minify=False, silent=True)

    Given a dict in the format ``{'path': "source code"}``, compiles the contracts and returns the formatted `build data <compile-json>`_.

    * ``contracts``: ``dict`` in the format ``{'path': "source code"}``
    * ``solc_version``: solc version to compile with. If ``None``, each contract is compiled with the latest installed version that matches the pragma.
    * ``optimize``: Toggle compiler optimization
    * ``runs``: Number of compiler optimization runs
    * ``evm_version``: EVM version to target. If ``None`` the compiler default is used.
    * ``minify``: Should contract sources be `minified <sources-minify>`_?
    * ``silent``: Toggle console verbosity

    Calling this method is roughly equivalent to the following:

    .. code-block:: python

        >>> from brownie.project import compiler

        >>> input_json = compiler.generate_input_json(contracts)
        >>> output_json = compiler.compile_from_input_json(input_json)
        >>> build_json = compiler.generate_build_json(input_json, output_json)

.. py:method:: compiler.find_solc_versions(contracts, install_needed=False, install_latest=False, silent=True)

    Analyzes contract pragmas and determines which solc version(s) to use.

    * ``contracts``: ``dict`` in the format ``{'path': "source code"}``
    * ``install_needed``: if ``True``, solc is installed when no installed version matches a contract pragma
    * ``install_latest``: if ``True``, solc is installed when a newer version is available than the installed one
    * ``silent``: enables verbose reporting

    Returns a ``dict`` of ``{'version': ["path", "path", ..]}``.

.. py:method:: compiler.generate_input_json(contracts, optimize=True, runs=200, evm_version=None, minify=False)

    Generates a `standard solc input JSON <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#input-description>`_ as a dict.


.. py:method:: compiler.compile_from_input_json(input_json, silent=True)

    Compiles from an input JSON and returns a `standard solc output JSON <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#output-description>`_ as a dict.

.. py:method:: compiler.generate_build_json(input_json, output_json, compiler_data={}, silent=True)

    Formats input and output compiler JSONs and returns a Brownie `build JSON <compile-json>`_ dict.

    * ``input_json``: Compiler input JSON dict
    * ``output_json``: Computer output JSON dict
    * ``compiler_data``: Additional compiler data to include
    * ``silent``: Toggles console verbosity

Internals
---------

These are more low-level methods, called internally during the execution of the above.

.. py:method:: compiler.generate_coverage_data(source_map, opcodes, contract_node, statement_nodes, branch_nodes)

    Generates the `program counter <compile-pc-map>`_ and `coverage <compile-coverage-map>`_ maps that are used by Brownie for debugging and test coverage evaluation.

    Takes the following arguments:

    * ``source_map``: `deployed source mapping <https://solidity.readthedocs.io/en/latest/miscellaneous.html#source-mappings>`_ as given by the compiler
    * ``opcodes``: deployed bytecode opcodes string as given by the compiler
    * ``contract_node``: py-solc-ast contract node object
    * ``statement_nodes``: list of statement node objects from ``compiler.get_statment_nodes``
    * ``branch_nodes``: list of branch node objects from ``compiler.get_branch_nodes``

    Returns:

    * ``pc_list``: program counter map
    * ``statement_map``: statement coverage map
    * ``branch_map``: branch coverage map

.. py:method:: compiler.get_statement_nodes(source_nodes)

    Given a list of AST source node objects from `py-solc-ast <https://github.com/iamdefinitelyahuman/py-solc-ast>`_, returns a list of statement nodes.  Used to generate the statement coverage map.

.. py:method:: compiler.get_branch_nodes(source_nodes)

    Given a list of AST source node objects from `py-solc-ast <https://github.com/iamdefinitelyahuman/py-solc-ast>`_, returns a list of branch nodes.  Used to generate the branch coverage map.

.. py:method:: compiler.format_link_references(evm)

    Standardizes formatting for unlinked library placeholders within bytecode. Used internally to ensure that unlinked libraries are represented uniformly regardless of the compiler version used.

    * ``evm``: The ``'evm'`` object from a compiler output JSON.

.. py:method:: compiler.get_bytecode_hash(bytecode)

    Removes the final metadata from a bytecode hex string and returns a hash of the result. Used to check if a contract has changed when the source code is modified.

.. py:method:: compiler.expand_source_map(source_map)

    Returns an uncompressed source mapping as a list of lists where no values are omitted.

    .. code-block:: python

        >>> from brownie.project.compiler import expand_source_map
        >>> expand_source_map("1:2:1:-;:9;2:1:2;;;")
        [[1, 2, 1, '-'], [1, 9, 1, '-'], [2, 1, 2, '-'], [2, 1, 2, '-'], [2, 1, 2, '-'], [2, 1, 2, '-']]

``brownie.project.scripts``
===========================

The ``scripts`` module contains methods for comparing, importing and executing python scripts related to a project.

.. py:method:: scripts.run(script_path, method_name="main", args=None, kwargs=None, gas_profile=False)

    Imports a project script, runs a method in it and returns the result.

    ``script_path``: path of script to import
    ``method_name``: name of method in the script to run
    ``args``: method args
    ``kwargs``: method kwargs
    ``gas_profile``: if ``True``, gas use data will be displayed when the script completes

    .. code-block:: python

        >>> from brownie import run
        >>> run('token')

        Running 'scripts.token.main'...

        Transaction sent: 0xeb9dfb6d97e8647f824a3031bc22a3e523d03e2b94674c0a8ee9b3ff601f967b
        Token.constructor confirmed - block: 1   gas used: 627391 (100.00%)
        Token deployed at: 0x8dc446C44C821F27B333C1357990821E07189E35


.. py:method:: scripts.get_ast_hash(path)

    Returns a hash based on the AST of a script and any scripts that it imports. Used to determine if a project script has been altered since it was last run.

    ``path``: path of the script

    .. code-block:: python

        >>> from brownie.project.scripts import get_ast_hash
        >>> get_ast_hash('scripts/deploy.py')
        '12b57e7bb8d88e3f289e27ba29e5cc28eb110e45'

``brownie.project.sources``
===========================

The ``sources`` module contains methods to access project source code files and information about them.

Module Methods
--------------

.. py:method:: sources.get(name)

    Returns the source code file for the given name. ``name`` can be a path or a contract name.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get('SafeMath')
        "pragma solidity ^0.5.0; ..."

.. py:method:: sources.get_path_list()

    Returns a list of contract source paths for the active project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_path_list()
        ['contracts/Token.sol', 'contracts/SafeMath.sol']

.. py:method:: sources.get_contract_list()

    Returns a list of contract names for the active project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_contract_list()
        ['Token', 'SafeMath']

.. py:method:: sources.load(project_path)

    Loads all source files for the given project path. Raises ``ContractExists`` if two source files contain contracts with the same name.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.load('my_projects/token')

.. py:method:: sources.clear()

    Clears all currently loaded source files.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.clear()

.. py:method:: sources.compile_source(source)

    Compiles source code given as a string and adds it to the available sources. The path will be set to ``<string-X>`` where X is an integer staring at one.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> source.compile_source('...')

.. py:method:: sources.get_hash(contract_name)

    Returns a hash of the contract source code.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_hash('Token')
        'da39a3ee5e6b4b0d3255bfef95601890afd80709'

.. py:method:: sources.get_source_path(contract_name)

    Returns the path to the file where a contract is located.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_source_path('Token')
        'contracts/Token.sol'

.. py:method: sources.get_highlighted_source(path, offset, pad=3)

    Given a path, start and stop offset, returns highlighted source code. Called internally by ``TransactionReceipt.source``.

.. _sources-minify:

.. py:method:: sources.minify(source)

    Given contract source as a string, returns a minified version and an offset map used internally to translate minified offsets to the original ones.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> token_source = sources.get('Token')
        >>> source.minify(token_source)
        "pragma solidity^0.5.0;\nimport"./SafeMath.sol";\ncontract Token{\nusing SafeMath for uint256; ..."


.. py:method:: sources.is_inside_offset(inner, outer)

    Returns a boolean indicating if the first offset is contained completely within the second offset.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.is_inside_offset([100, 200], [100, 250])
        True

.. py:method:: sources.expand_offset(contract_name, offset)

    Converts a minified offset to one that matches the current source code.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.expand_offset("Token", [1258, 1466])
        (2344, 2839)
