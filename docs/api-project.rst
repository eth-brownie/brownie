.. _api-project:

===========
Project API
===========

The ``project`` package contains methods for initializing, loading and compiling Brownie projects, and container classes to hold the data.

When Brownie is loaded from within a project folder, that project is automatically loaded and the :func:`ContractContainer <brownie.network.contract.ContractContainer>` objects are added to the ``__main__`` namespace. Unless you are working with more than one project at the same time, there is likely no need to directly interact with the top-level :func:`Project <brownie.project.main.Project>` object or any of the methods within this package.

Only the ``project.main`` module contains methods that directly interact with the filesystem.

``brownie.project.main``
========================

The ``main`` module contains the high-level methods and classes used to create, load, and close projects. All of these methods are available directly from ``brownie.project``.

Project
-------

.. py:class:: brownie.project.main.Project

    Top level container that holds all objects related to a Brownie project.

Project Methods
***************

.. py:classmethod:: Project.load()

    Collects project source files, compiles new or updated contracts, instantiates :func:`ContractContainer <brownie.network.contract.ContractContainer>` objects, and populates the namespace.

    Projects are typically loaded via :func:`project.load <main.load>`, but if you have a :func:`Project <brownie.project.main.Project>` object that was previously closed you can reload it using this method.

.. py:classmethod:: Project.load_config()

    Updates the configuration settings from the ``brownie-config.yaml`` file within this project's root folder.

.. py:classmethod:: Project.close(raises = True)

    Removes this object and the related :func:`ContractContainer <brownie.network.contract.ContractContainer>` objects from the namespace.

    .. code-block:: python

        >>> from brownie.project import TokenProject
        >>> TokenProject.close()
        >>> TokenProject
        NameError: name 'TokenProject' is not defined

.. py:classmethod:: Project.dict()

    Returns a dictionary of :func:`ContractContainer <brownie.network.contract.ContractContainer>` objects.

    .. code-block:: python

        >>> from brownie.project import TokenProject
        >>> TokenProject.dict()
        {
           'Token': [],
           'SafeMath': []
        }

TempProject
-----------

.. py:class:: brownie.project.main.TempProject

    Simplified version of :func:`Project <brownie.project.main.Project>`, used to hold contracts that are compiled via :func:`project.compile_source <main.compile_source>`. Instances of this class are not included in the list of active projects or automatically placed anywhere within the namespace.

Module Methods
--------------

.. py:method:: main.check_for_project(path)

    Checks for an existing Brownie project within a folder and it's parent folders, and returns the base path to the project as a ``Path`` object.  Returns ``None`` if no project is found.

    Accepts a path as a str or a ``Path`` object.

    .. code-block:: python

        >>> from brownie import project
        >>> Path('.').resolve()
        PosixPath('/my_projects/token/build/contracts')
        >>> project.check_for_project('.')
        PosixPath('/my_projects/token')

.. py:method:: main.get_loaded_projects()

    Returns a list of currently loaded :func:`Project <brownie.project.main.Project>` objects.

    .. code-block:: python

        >>> from brownie import project
        >>> project.get_loaded_projects()
        [<Project object 'TokenProject'>, <Project object 'OtherProject'>]

.. py:method:: main.new(project_path=".", ignore_subfolder=False)

    Initializes a new project at the given path.  If the folder does not exist, it will be created.

    Returns the path to the project as a string.

    .. code-block:: python

        >>> from brownie import project
        >>> project.new('/my_projects/new_project')
        '/my_projects/new_project'

.. py:method:: main.from_brownie_mix(project_name, project_path=None, ignore_subfolder=False)

    Initializes a new project via a template. Templates are downloaded from the `Brownie Mix github repo <https://github.com/brownie-mix>`_.

    If no path is given, the project will be initialized in a subfolder of the same name.

    Returns the path to the project as a string.

    .. code-block:: python

        >>> from brownie import project
        >>> project.from_brownie_mix('token')
        Downloading from https://github.com/brownie-mix/token-mix/archive/master.zip...
        'my_projects/token'

.. py:method:: main.load(project_path=None, name=None)

    Loads a Brownie project and instantiates various related objects.

    * ``project_path``: Path to the project. If ``None``, attempts to find one using ``check_for_project('.')``.
    * ``name``: Name to assign to the project. If None, the name is generated from the name of the project folder.

    Returns a :func:`Project <brownie.project.main.Project>` object. The same object is also available from within the ``project`` module namespce.

    .. code-block:: python

        >>> from brownie import project
        >>> project.load('/my_projects/token')
        [<Project object 'TokenProject'>]
        >>> project.TokenProject
        <Project object 'TokenProject'>
        >>> project.TokenProject.Token
        <ContractContainer object 'Token'>

.. py:method:: main.compile_source(source, solc_version=None, optimize=True, runs=200, evm_version=None)

    Compiles the given source code string and returns a :func:`TempProject <brownie.project.main.TempProject>` object.

    If Vyper source code is given, the contract name will be ``Vyper``.

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
        <TempProject object>
        >>> container.SimpleTest
        <ContractContainer object 'SimpleTest'>

.. py:method:: main.install_package(package_id)

    Install a package.

    See the :ref:`Brownie Package Manager <package-manager>` documentation for more information on packages.

    * ``package_id``: Package identifier

``brownie.project.build``
=========================

The ``build`` module contains classes and methods used internally by Brownie to interact with files in a project's ``build/contracts`` folder.

Build
-----

.. py:class:: brownie.project.build.Build

    Container that stores and manipulates build data loaded from the ``build/contracts/`` files of a specific project. It is instantiated automatically when a project is opened, and available within the :func:`Project <brownie.project.main.Project>` object as ``Project._build``.

.. code-block:: python

    >>> from brownie.project import TokenProject
    >>> TokenProject._build
    <brownie.project.build.Build object at 0x7fb74cb1b2b0>

Build Methods
*************

.. py:classmethod:: Build.get(contract_name)

    Returns build data for the given contract name.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.get('Token')
        {...}

.. py:classmethod:: Build.items(path=None)

    Provides an list of tuples in the format ``('contract_name', build_json)``, similar to calling ``dict.items``.  If a path is given, only contracts derived from that source file are returned.

    .. code-block:: python

        >>> from brownie.project import build
        >>> for name, data in build.items():
        ...     print(name)
        Token
        SafeMath

.. py:classmethod:: Build.contains(contract_name)

    Checks if a contract with the given name is in the currently loaded build data.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.contains('Token')
        True

.. py:classmethod:: Build.get_dependents(contract_name)

    Returns a list of contracts that inherit or link to the given contract name. Used by the compiler when determining which contracts to recompile based on a changed source file.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.get_dependents('Token')
        ['SafeMath']

Build Internal Methods
**********************

.. py:classmethod:: Build._add(build_json)

    Adds a contract's build data to the container.

.. py:classmethod:: Build._remove(contract_name)

    Removes a contract's build data from the container.

.. py:classmethod:: Build._generate_revert_map(pcMap)

    Adds a contract's dev revert strings to the revert map and it's ``pcMap``. Called internally when adding a new contract.

    The revert map is dict of tuples, where each key is a program counter that contains a ``REVERT`` or ``INVALID`` operation for a contract in the active project. When a transaction reverts, the dev revert string can be determined by looking up the final program counter in this mapping.

    Each value is a 5 item tuple of: ``("path/to/source", (start, stop), "function name", "dev: revert string", self._source)``

    When two contracts have differing values for the same program counter, the value in the revert map is set to ``False``. If a transaction reverts with this pc, the entire trace must be queried to determine which contract reverted and get the dev string from it's ``pcMap``.

Internal Methods
----------------

The following methods exist outside the scope of individually loaded projects.

.. py:method:: build._get_dev_revert(pc)

    Given the program counter from a stack trace that caused a transaction to revert, returns the :ref:`commented dev string <dev-revert>` (if any). Used by :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>`.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.get_dev_revert(1847)
        "dev: zero value"

.. py:method:: build._get_error_source_from_pc(pc)

    Given the program counter from a stack trace that caused a transaction to revert, returns the highlighted relevent source code and the name of the method that reverted.

    Used by :func:`TransactionReceipt <brownie.network.transaction.TransactionReceipt>` when generating a :func:`VirtualMachineError <brownie.exceptions.VirtualMachineError>`.

``brownie.project.compiler``
============================

The ``compiler`` module contains methods for compiling contracts, and formatting the compiled data. This module is used internally whenever a Brownie project is loaded.

In most cases you will not need to call methods in this module directly. Instead you should use :func:`project.load <main.load>` to compile your project initially and :func:`project.compile_source <main.compile_source>` for adding individual, temporary contracts. Along with compiling, these methods also add the returned data to :func:`Project._build <brownie.project.build.Build>` and return :func:`ContractContainer <brownie.network.contract.ContractContainer>` objects.

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

.. py:method:: compiler.compile_and_format(contract_sources, solc_version=None, optimize=True, runs=200, evm_version=None, silent=True, allow_paths=None)

    Given a dict in the format ``{'path': "source code"}``, compiles the contracts and returns the formatted `build data <compile-json>`_.

    * ``contract_sources``: ``dict`` in the format ``{'path': "source code"}``
    * ``solc_version``: solc version to compile with. If ``None``, each contract is compiled with the latest installed version that matches the pragma.
    * ``optimize``: Toggle compiler optimization
    * ``runs``: Number of compiler optimization runs
    * ``evm_version``: EVM version to target. If ``None`` the compiler default is used.
    * ``silent``: Toggle console verbosity
    * ``allow_paths``: Import path, passed to `solc` as an additional path that contract files may be imported from

    Calling this method is roughly equivalent to the following:

    .. code-block:: python

        >>> from brownie.project import compiler

        >>> input_json = compiler.generate_input_json(contract_sources)
        >>> output_json = compiler.compile_from_input_json(input_json)
        >>> build_json = compiler.generate_build_json(input_json, output_json)

.. py:method:: compiler.find_solc_versions(contract_sources, install_needed=False, install_latest=False, silent=True)

    Analyzes contract pragmas and determines which solc version(s) to use.

    * ``contract_sources``: ``dict`` in the format ``{'path': "source code"}``
    * ``install_needed``: if ``True``, solc is installed when no installed version matches a contract pragma
    * ``install_latest``: if ``True``, solc is installed when a newer version is available than the installed one
    * ``silent``: enables verbose reporting

    Returns a ``dict`` of ``{'version': ["path", "path", ..]}``.

.. py:method:: compiler.find_best_solc_version(contract_sources, install_needed=False, install_latest=False, silent=True)

    Analyzes contract pragmas and finds the best version compatible with all sources.

    * ``contract_sources``: ``dict`` in the format ``{'path': "source code"}``
    * ``install_needed``: if ``True``, solc is installed when no installed version matches a contract pragma
    * ``install_latest``: if ``True``, solc is installed when a newer version is available than the installed one
    * ``silent``: enables verbose reporting

    Returns a ``dict`` of ``{'version': ["path", "path", ..]}``.

.. py:method:: compiler.generate_input_json(contract_sources, optimize=True, runs=200, evm_version=None, language="Solidity")

    Generates a `standard solc input JSON <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#input-description>`_ as a dict.

.. py:method:: compiler.compile_from_input_json(input_json, silent=True, allow_paths=None)

    Compiles from an input JSON and returns a `standard solc output JSON <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#output-description>`_ as a dict.

.. py:method:: compiler.generate_build_json(input_json, output_json, compiler_data={}, silent=True)

    Formats input and output compiler JSONs and returns a Brownie `build JSON <compile-json>`_ dict.

    * ``input_json``: Compiler input JSON dict
    * ``output_json``: Computer output JSON dict
    * ``compiler_data``: Additional compiler data to include
    * ``silent``: Toggles console verbosity

``brownie.project.scripts``
===========================

The ``scripts`` module contains methods for comparing, importing and executing python scripts related to a project.

.. py:method:: scripts.run(script_path, method_name="main", args=None, kwargs=None, project=None)

    Imports a project script, runs a method in it and returns the result.

    ``script_path``: path of script to import
    ``method_name``: name of method in the script to run
    ``args``: method args
    ``kwargs``: method kwargs
    ``project``: :func:`Project <brownie.project.main.Project>` object that should available for import into the script namespace

    .. code-block:: python

        >>> from brownie import run
        >>> run('token')

        Running 'scripts.token.main'...

        Transaction sent: 0xeb9dfb6d97e8647f824a3031bc22a3e523d03e2b94674c0a8ee9b3ff601f967b
        Token.constructor confirmed - block: 1   gas used: 627391 (100.00%)
        Token deployed at: 0x8dc446C44C821F27B333C1357990821E07189E35

Internal Methods
----------------

.. py:method:: scripts._get_ast_hash(path)

    Returns a hash based on the AST of a script and any scripts that it imports. Used to determine if a project script has been altered since it was last run.

    ``path``: path of the script

    .. code-block:: python

        >>> from brownie.project.scripts import get_ast_hash
        >>> get_ast_hash('scripts/deploy.py')
        '12b57e7bb8d88e3f289e27ba29e5cc28eb110e45'

``brownie.project.sources``
===========================

The ``sources`` module contains classes and methods to access project source code files and information about them.

Sources
-------

.. py:class:: brownie.project.sources.Sources

    The ``Sources`` object provides access to the ``contracts/`` and ``interfaces/`` files for a specific project. It is instantiated automatically when a project is loaded, and available within the :func:`Project <brownie.project.main.Project>` object as ``Project._sources``.

    .. code-block:: python

        >>> from brownie.project import TokenProject
        >>> TokenProject._sources
        <brownie.project.sources.Sources object at 0x7fb74cb1bb70>

.. py:classmethod:: Sources.get(name)

    Returns the source code file for the given name. ``name`` can be a path or a contract name.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get('SafeMath')
        "pragma solidity ^0.5.0; ..."

.. py:classmethod:: Sources.get_path_list()

    Returns a sorted list of contract source paths for the project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_path_list()
        ['contracts/SafeMath.sol', 'contracts/Token.sol', 'interfaces/IToken.sol']

.. py:classmethod:: Sources.get_contract_list()

    Returns a sorted list of contract names for the project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_contract_list()
        ['SafeMath', 'Token']

.. py:classmethod:: Sources.get_interface_list()

    Returns a sorted list of interface names for the project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_interface_list()
        ['IToken']

.. py:classmethod:: Sources.get_interface_hashes

    Returns a dict of interface hashes in the form of ``{'interfaceName': "hash"}``

.. py:classmethod:: Sources.get_interface_sources

    Returns a dict of interfaces sources in the form ``{'path/to/interface': "source code"}``

.. py:classmethod:: Sources.get_source_path(contract_name)

    Returns the path to the file where a contract or interface is located.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_source_path('Token')
        'contracts/Token.sol'


Module Methods
--------------

.. py:method:: sources.is_inside_offset(inner, outer)

    Returns a boolean indicating if the first offset is contained completely within the second offset.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.is_inside_offset([100, 200], [100, 250])
        True

.. py:method: sources.highlighted_source(path, offset, pad=3)

    Given a path, start and stop offset, returns highlighted source code. Called internally by :func:`TransactionReceipt.source <TransactionReceipt.source>`.

.. py:method:: sources.get_contracts(full_source)

    Given a Solidity contract source as a string, returns a ``dict`` of source code for individual contracts.

    .. code-block:: python

        >>> from brownie.project.sources import get_contracts
        >>> get_contracts('''
        ... pragma solidity 0.5.0;
        ...
        ... contract Foo {
        ...     function bar() external returns (bool) {
        ...         return true;
        ...     }
        ... }
        ...
        ... library Bar {
        ...     function baz(uint a, uint b) external pure returns (uint) {
        ...         return a + b;
        ...     }
        ... }''')
        {
            'Foo': 'contract Foo {\n    function bar() external returns (bool) {\n        return true;\n    }\n}',
            'Bar': 'library Bar {\n    function baz(uint a, uint b) external pure returns (uint) {\n        return a + b;\n    }\n}'
        }

.. py:method:: sources.get_pragma_spec(source, path=None)

    Returns an `NpmSpec <https://python-semanticversion.readthedocs.io/en/latest/#npm-based-ranges>`_ object representing the first pragma statement found within a source file.

    Raises :func:`PragmaError <brownie.exceptions.PragmaError>` on failure. If ``path`` is not ``None``, it will be included in the error string.
