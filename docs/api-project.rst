.. _api-project:

===========
Project API
===========

The ``project`` package contains methods for initializing, loading and compiling Brownie projects, and container classes to hold the data.

When Brownie is loaded from within a project folder, that project is automatically loaded and the ``ContractContainer`` objects are added to the ``__main__`` namespace. Unless you are working with more than one project at the same time, there is likely no need to directly interact with the top-level ``Project`` object or any of the methods within this package.

Only the ``project.main`` module contains methods that directly interact with the filesystem.

``brownie.project.main``
========================

The ``main`` module contains the high-level methods and classes used to create, load, and close projects. All of these methods are available directly from ``brownie.project``.

.. _api-project-project:

Project
-------

The ``Project`` class is the top level container that holds all objects related to a Brownie project.

Project Methods
***************

.. py:classmethod:: Project.load() -> None

    Compiles the project source codes, instantiates ``ContractContainer`` objects, and populates the namespace.

    Projects are typically loaded via ``brownie.project.load()``, but if you have a ``Project`` object that was previously closed you can reload it using this method.

.. py:classmethod:: Project.load_config() -> None

    Updates the configuration settings from the ``brownie-config.yaml`` file within this project's root folder.

.. py:classmethod:: Project.close(raises: bool = True) -> None

    Removes this object and the related ``ContractContainer`` objects from the namespace.

    .. code-block:: python

        >>> from brownie.project import TokenProject
        >>> TokenProject.close()
        >>> TokenProject
        NameError: name 'TokenProject' is not defined

.. py:classmethod:: Project.dict()

    Returns a dictionary of ``ContractContainer`` objects.

    .. code-block:: python

        >>> from brownie.project import TokenProject
        >>> TokenProject.dict()
        {
           'Token': [],
           'SafeMath': []
        }

TempProject
-----------

``TempProject`` is a simplified version of ``Project``, used to hold contracts that are compiled via ``main.compile_sources``. Instances of this class are not included in the list of active projects or automatically placed anywhere within the namespace.

Module Methods
--------------

.. py:method:: main.check_for_project(path: Union[str, 'Path']) -> Optional[Path]

    Checks for an existing Brownie project within a folder and it's parent folders, and returns the base path to the project as a ``Path`` object.  Returns ``None`` if no project is found.

    Accepts a path as a str or a ``Path`` object.

    .. code-block:: python

        >>> from brownie import project
        >>> Path('.').resolve()
        PosixPath('/my_projects/token/build/contracts')
        >>> project.check_for_project('.')
        PosixPath('/my_projects/token')

.. py:method:: main.get_loaded_projects() -> List

    Returns a list of currently loaded ``Project`` objects.

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

.. py:method:: main.from_ethpm(uri):

    Generates a ``TempProject`` from an ethPM package.

    * ``uri``: ethPM manifest URI. Format can be ERC1319 or IPFS.

.. py:method:: main.load(project_path=None, name=None)

    Loads a Brownie project and instantiates various related objects.

    * ``project_path``: Path to the project. If ``None``, attempts to find one using ``check_for_project('.')``.
    * ``name``: Name to assign to the project. If None, the name is generated from the name of the project folder.

    Returns a ``Project`` object. The same object is also available from within the ``project`` module namespce.

    .. code-block:: python

        >>> from brownie import project
        >>> project.load('/my_projects/token')
        [<Project object 'TokenProject'>]
        >>> project.TokenProject
        <Project object 'TokenProject'>
        >>> project.TokenProject.Token
        <ContractContainer object 'Token'>

.. py:method:: main.compile_source(source, solc_version=None, optimize=True, runs=200, evm_version=None)

    Compiles the given Solidity source code string and returns a ``TempProject`` object.

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

.. _api-project-build:

``brownie.project.build``
=========================

The ``build`` module contains classes and methods used internally by Brownie to interact with files in a project's ``build/contracts`` folder.

.. _api-project-build-build:

Build
-----

The ``Build`` object is a container that stores and manipulates build data loaded from the ``build/contracts/`` files of a specific project. It is instantiated automatically when a project is opened, and available within the :ref:`api-project-project` object as ``Project._build``.

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

.. py:classmethod:: Build.expand_build_offsets(build_json)

    Given a build json as a dict, expands the minified offsets to match the original source code.

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

    Given the program counter from a stack trace that caused a transaction to revert, returns the :ref:`commented dev string <dev-revert>` (if any). Used by ``TransactionReceipt``.

    .. code-block:: python

        >>> from brownie.project import build
        >>> build.get_dev_revert(1847)
        "dev: zero value"

.. py:method:: build._get_error_source_from_pc(pc)

    Given the program counter from a stack trace that caused a transaction to revert, returns the highlighted relevent source code and the name of the method that reverted.

    Used by ``TransactionReceipt`` when generating a ``VirtualMachineError``.

``brownie.project.compiler``
============================

The ``compiler`` module contains methods for compiling contracts, and formatting the compiled data. This module is used internally whenever a Brownie project is loaded.

In most cases you will not need to call methods in this module directly. Instead you should use ``project.load`` to compile your project initially and ``project.compile_source`` for adding individual, temporary contracts. Along with compiling, these methods also add the returned data to ``project.build`` and return ``ContractContainer`` objects.

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

.. py:method:: compiler.compile_and_format(contract_sources, solc_version=None, optimize=True, runs=200, evm_version=None, minify=False, silent=True, allow_paths=None)

    Given a dict in the format ``{'path': "source code"}``, compiles the contracts and returns the formatted `build data <compile-json>`_.

    * ``contract_sources``: ``dict`` in the format ``{'path': "source code"}``
    * ``solc_version``: solc version to compile with. If ``None``, each contract is compiled with the latest installed version that matches the pragma.
    * ``optimize``: Toggle compiler optimization
    * ``runs``: Number of compiler optimization runs
    * ``evm_version``: EVM version to target. If ``None`` the compiler default is used.
    * ``minify``: Should contract sources be `minified <sources-minify>`_?
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

.. py:method:: compiler.generate_input_json(contract_sources, optimize=True, runs=200, evm_version=None, minify=False)

    Generates a `standard solc input JSON <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#input-description>`_ as a dict.

.. py:method:: compiler.compile_from_input_json(input_json, silent=True, allow_paths=None)

    Compiles from an input JSON and returns a `standard solc output JSON <https://solidity.readthedocs.io/en/latest/using-the-compiler.html#output-description>`_ as a dict.

.. py:method:: compiler.generate_build_json(input_json, output_json, compiler_data={}, silent=True)

    Formats input and output compiler JSONs and returns a Brownie `build JSON <compile-json>`_ dict.

    * ``input_json``: Compiler input JSON dict
    * ``output_json``: Computer output JSON dict
    * ``compiler_data``: Additional compiler data to include
    * ``silent``: Toggles console verbosity

Internal Methods
----------------

.. py:method:: compiler._format_link_references(evm)

    Standardizes formatting for unlinked library placeholders within bytecode. Used internally to ensure that unlinked libraries are represented uniformly regardless of the compiler version used.

    * ``evm``: The ``'evm'`` object from a compiler output JSON.

.. py:method:: compiler._get_bytecode_hash(bytecode)

    Removes the final metadata from a bytecode hex string and returns a hash of the result. Used to check if a contract has changed when the source code is modified.

.. py:method:: compiler._expand_source_map(source_map)

    Returns an uncompressed source mapping as a list of lists where no values are omitted.

    .. code-block:: python

        >>> from brownie.project.compiler import expand_source_map
        >>> expand_source_map("1:2:1:-;:9;2:1:2;;;")
        [[1, 2, 1, '-'], [1, 9, 1, '-'], [2, 1, 2, '-'], [2, 1, 2, '-'], [2, 1, 2, '-'], [2, 1, 2, '-']]

.. py:method:: compiler._generate_coverage_data(source_map_str, opcodes_str, contract_node, stmt_nodes, branch_nodes, has_fallback)

    Generates the `program counter <compile-pc-map>`_ and `coverage <compile-coverage-map>`_ maps that are used by Brownie for debugging and test coverage evaluation.

    Takes the following arguments:

    * ``source_map_str``: `deployed source mapping <https://solidity.readthedocs.io/en/latest/miscellaneous.html#source-mappings>`_ as given by the compiler
    * ``opcodes_str``: deployed bytecode opcodes string as given by the compiler
    * ``contract_node``: py-solc-ast contract node object
    * ``stmt_nodes``: list of statement node objects from ``compiler.get_statment_nodes``
    * ``branch_nodes``: list of branch node objects from ``compiler.get_branch_nodes``
    * ``has_fallback``: Bool, does this contract contain a fallback method?

    Returns:

    * ``pc_list``: program counter map
    * ``statement_map``: statement coverage map
    * ``branch_map``: branch coverage map

.. py:method:: compiler._get_statement_nodes(source_nodes)

    Given a list of AST source node objects from `py-solc-ast <https://github.com/iamdefinitelyahuman/py-solc-ast>`_, returns a list of statement nodes.  Used to generate the statement coverage map.

.. py:method:: compiler._get_branch_nodes(source_nodes)

    Given a list of AST source node objects from `py-solc-ast <https://github.com/iamdefinitelyahuman/py-solc-ast>`_, returns a list of branch nodes.  Used to generate the branch coverage map.

``brownie.project.ethpm``
=========================

The ``ethpm`` module contains methods for interacting with ethPM manifests and registries. See :ref:`eth-pm` for more detailed information on how to access this functionality.

Module Methods
--------------

.. py:method:: ethpm.get_manifest(uri)

    Fetches an ethPM manifest and processes it for use with Brownie. A local copy is also stored if the given URI follows the ERC1319 spec.

    * ``uri``: URI location of the manifest. Can be IPFS or ERC1319.

.. py:method:: ethpm.process_manifest(manifest, uri)

    Processes a manifest for use with Brownie.

    * ``manifest``: ethPM manifest
    * ``uri``: IPFS uri of the package

.. py:method:: ethpm.get_deployment_addresses(manifest, contract_name, genesis_hash)

    Parses a manifest and returns a list of deployment addresses for the given contract and chain.

    * ``manifest``: ethPM manifest
    * ``contract_name``: Name of the contract
    * ``genesis_block``: Genesis block hash for the chain to return deployments on. If ``None``, the currently active chain will be used.

.. py:method:: ethpm.get_installed_packages(project_path)

    Returns information on installed ethPM packages within a project.

    * ``project_path``: Path to the root folder of the project

    Returns:

    * ``[(project name, version), ..]`` of installed packages
    * ``[(project name, version), ..]`` of installed-but-modified packages

.. py:method:: ethpm.install_package(project_path, uri, replace_existing)

    Installs an ethPM package within the project.

    * ``project_path``: Path to the root folder of the project
    * ``uri``: manifest URI, can be erc1319 or ipfs
    * ``replace_existing``: if True, existing files will be overwritten when installing the package

    Returns the package name as a string.

.. py:method:: ethpm.remove_package(project_path, package_name, delete_files)

    Removes an ethPM package from a project.

    * ``project_path``: Path to the root folder of the project
    * ``package_name``: name of the package
    * ``delete_files``: if ``True``, source files related to the package are deleted. Files that are still required by other installed packages will not be deleted.

    Returns a boolean indicating if the package was installed.

.. py:method:: ethpm.create_manifest(project_path, package_config, pin_assets=False, silent=True)

    Creates a manifest from a project, and optionally pins it to IPFS.

    * ``project_path``: Path to the root folder of the project
    * ``package_config``: Configuration settings for the manifest
    * ``pin_assets``: if ``True``, all source files and the manifest will be uploaded onto IPFS via Infura.

    Returns: ``(generated manifest, ipfs uri of manifest)``

.. py:method:: ethpm.verify_manifest(package_name, version, uri)

    Verifies the validity of a package at a given IPFS URI.

    * ``package_name``: Package name
    * ``version``: Package version
    * ``uri``: IPFS uri

    Raises ``InvalidManifest`` if the manifest is not valid.

.. py:method:: ethpm.release_package(registry_address, account, package_name, version, uri)

    Creates a new release of a package at an ERC1319 registry.

    * ``registry_address``: Address of the registry
    * ``account``: ``Account`` object used to broadcast the transaction to the registry
    * ``package_name``: Name of the package
    * ``version``: Package version
    * ``uri``: IPFS uri of the package

    Returns the ``TransactionReceipt`` of the registry call to release the package.

``brownie.project.scripts``
===========================

The ``scripts`` module contains methods for comparing, importing and executing python scripts related to a project.

.. py:method:: scripts.run(script_path, method_name="main", args=None, kwargs=None, project=None)

    Imports a project script, runs a method in it and returns the result.

    ``script_path``: path of script to import
    ``method_name``: name of method in the script to run
    ``args``: method args
    ``kwargs``: method kwargs
    ``project``: ``Project`` object that should available for import into the script namespace

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

The ``Sources`` object provides access to the ``contracts/`` files for a specific project. It is instantiated automatically when a project is opened, and available within the :ref:`api-project-project` object as ``Project._sources``.

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

    Returns a list of contract source paths for the active project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_path_list()
        ['contracts/Token.sol', 'contracts/SafeMath.sol']

.. py:classmethod:: Sources.get_contract_list()

    Returns a list of contract names for the active project.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_contract_list()
        ['Token', 'SafeMath']

.. py:classmethod:: Sources.get_source_path(contract_name)

    Returns the path to the file where a contract is located.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.get_source_path('Token')
        'contracts/Token.sol'

.. py:classmethod:: Sources.expand_offset(contract_name, offset)

    Converts a minified offset to one that matches the current source code.

    .. code-block:: python

        >>> from brownie.project import sources
        >>> sources.expand_offset("Token", [1258, 1466])
        (2344, 2839)

Module Methods
--------------

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

.. py:method: sources.highlighted_source(path, offset, pad=3)

    Given a path, start and stop offset, returns highlighted source code. Called internally by ``TransactionReceipt.source``.

.. py:method:: sources.get_hash(source, contract_name, minified)

    Returns a sha1 hash generated from a contract's source code.
